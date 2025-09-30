"""Olive Young 제품 정보 스크래퍼 (Playwright 기반)"""
import asyncio
from typing import Optional
from loguru import logger
from playwright.async_api import async_playwright, Page, Browser


class ProductInfo:
    """제품 정보 데이터 클래스"""
    def __init__(self):
        self.name: Optional[str] = None
        self.price: Optional[str] = None
        self.rating: Optional[str] = None
        self.review_count: Optional[str] = None
        self.detail_images: list[str] = []
        self.review_rating_distribution: dict[int, str] = {}
        self.reviews: list[str] = []


class OliveYoungScraper:
    """Olive Young 제품 페이지 스크래퍼 (Playwright 기반)"""

    SELECTORS = {
        "name": "#Contents > div.prd_detail_box.renew > div.right_area > div > p.prd_name",
        "price": "#totalPrcTxt",
        "rating": "#repReview > b",
        "review_count": "#repReview > em",
        "detail_toggle": "#btn_toggle_detail_image",
        "review_button": "#reviewInfo > a",
        "sort_by_helpfulness_button": "#gdasSort > li:nth-child(2) > a",
    }

    def __init__(self, headless: bool = False):
        """
        Args:
            headless: 브라우저를 headless 모드로 실행할지 여부
        """
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.playwright = None

    async def __aenter__(self):
        """Async context manager entry"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=self.headless)
        self.page = await self.browser.new_page()

        # User agent 설정
        await self.page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.page:
            await self.page.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def scrape(self, url: str, max_reviews: int = 30) -> ProductInfo:
        """
        제품 페이지에서 정보를 스크래핑합니다.

        Args:
            url: Olive Young 제품 페이지 URL
            max_reviews: 최대 스크래핑할 리뷰 개수

        Returns:
            ProductInfo: 스크래핑된 제품 정보
        """
        if not self.page:
            raise RuntimeError("Scraper must be used as async context manager")

        logger.info(f"Scraping URL: {url}")
        await self.page.goto(url, wait_until="domcontentloaded", timeout=60000)

        product = ProductInfo()

        # 제품명
        try:
            product.name = await self._get_text(self.SELECTORS["name"])
            logger.info(f"제품명: {product.name}")
        except Exception as e:
            logger.warning(f"제품명 가져오기 실패: {e}")

        # 가격
        try:
            product.price = await self._get_text(self.SELECTORS["price"])
            logger.info(f"가격: {product.price}")
        except Exception as e:
            logger.warning(f"가격 가져오기 실패: {e}")

        # 리뷰 평점
        try:
            product.rating = await self._get_text(self.SELECTORS["rating"])
            logger.info(f"평점: {product.rating}")
        except Exception as e:
            logger.warning(f"평점 가져오기 실패: {e}")

        # 리뷰 개수
        try:
            product.review_count = await self._get_text(self.SELECTORS["review_count"])
            logger.info(f"리뷰 개수: {product.review_count}")
        except Exception as e:
            logger.warning(f"리뷰 개수 가져오기 실패: {e}")

        # 제품 상세정보 이미지
        try:
            product.detail_images = await self._get_detail_images()
            logger.info(f"상세 이미지 개수: {len(product.detail_images)}")
        except Exception as e:
            logger.warning(f"상세 이미지 가져오기 실패: {e}")

        # 리뷰 탭 클릭, 평점 분포 가져오기, 정렬 및 추출
        try:
            await self._click_review_tab()
            product.review_rating_distribution = await self._get_review_rating_distribution()
            await self._sort_reviews_by_helpfulness()

            # 페이지네이션하며 모든 리뷰 추출
            product.reviews = await self._paginate_and_extract_reviews(max_reviews=max_reviews)
            logger.info(f"총 {len(product.reviews)}개의 리뷰 추출 완료")

        except Exception as e:
            logger.warning(f"리뷰 정보 가져오기, 정렬 및 추출 실패: {e}")

        return product

    async def _paginate_and_extract_reviews(self, max_reviews: int) -> list[str]:
        """모든 리뷰 페이지를 돌며 최대 max_reviews개까지 리뷰를 추출합니다."""
        all_reviews = []
        while len(all_reviews) < max_reviews:
            # 현재 페이지 리뷰 추출
            reviews_on_page = await self._extract_reviews_from_page()
            if not reviews_on_page:
                logger.info("현재 페이지에 리뷰가 없어 페이지네이션을 중단합니다.")
                break
            
            for review in reviews_on_page:
                if len(all_reviews) < max_reviews:
                    all_reviews.append(review)
                else:
                    break
            
            if len(all_reviews) >= max_reviews:
                logger.info(f"최대 리뷰 개수({max_reviews})에 도달했습니다.")
                break

            # 다음 페이지로 이동
            try:
                paging_container = "#gdasContentsArea > div > div.pageing"
                # 현재 활성화된 페이지(<strong>)를 찾음
                current_page_element = await self.page.query_selector(f"{paging_container} > strong")
                if not current_page_element:
                    logger.info("활성화된 페이지 번호를 찾을 수 없어 중단합니다.")
                    break
                
                current_page_num = int((await current_page_element.text_content()).strip())

                # 다음 버튼 찾기
                next_button = None
                # 현재 페이지가 10, 20, ... 이면 '다음' 버튼 클릭
                if current_page_num % 10 == 0:
                    next_button = await self.page.query_selector(f"{paging_container} > a.next")
                # 그렇지 않으면 바로 다음 번호(<strong> 바로 다음 <a>) 클릭
                else:
                    next_button = await self.page.query_selector(f"{paging_container} > strong + a")

                if not next_button:
                    logger.info("마지막 페이지입니다. 리뷰 추출을 종료합니다.")
                    break

                button_text = (await next_button.text_content()).strip()
                logger.info(f"다음 페이지로 이동합니다: '{button_text}'")
                await next_button.click()
                # TODO: 페이지 로딩을 더 안정적으로 기다리는 방법으로 개선 필요
                await self.page.wait_for_timeout(2000)

            except Exception as e:
                logger.warning(f"페이지 이동 중 오류 발생: {e}. 페이지네이션을 중단합니다.")
                break
        
        return all_reviews

    async def _extract_reviews_from_page(self) -> list[str]:
        """현재 페이지의 리뷰 텍스트를 추출합니다."""
        reviews_on_page = []
        logger.info("현재 페이지의 리뷰 추출 시작")
        try:
            review_list_selector = "#gdasList"
            await self.page.wait_for_selector(review_list_selector, timeout=5000)

            review_elements = await self.page.query_selector_all(f"{review_list_selector} > li")
            logger.info(f"현재 페이지에서 {len(review_elements)}개의 리뷰 항목을 찾았습니다.")

            for i in range(1, len(review_elements) + 1):
                review_text_selector = f"#gdasList > li:nth-child({i}) > div.review_cont > div.txt_inner"
                try:
                    # wait_for_selector가 포함된 _get_text 사용
                    text = await self._get_text(review_text_selector, timeout=1000)
                    reviews_on_page.append(text)
                    logger.debug(f"{i}번째 리뷰 추출 성공.")
                except Exception:
                    # txt_inner가 없는 경우 (e.g. 포토리뷰)는 텍스트가 없으므로 건너뜀
                    logger.warning(f"{i}번째 리뷰에서 텍스트(.txt_inner)를 찾지 못했습니다. 포토리뷰일 수 있습니다.")
        
        except Exception as e:
            logger.error(f"리뷰 목록 추출 중 오류 발생: {e}")

        logger.info(f"현재 페이지에서 {len(reviews_on_page)}개의 리뷰 텍스트를 추출했습니다.")
        return reviews_on_page

    async def _sort_reviews_by_helpfulness(self):
        """리뷰를 '도움순'으로 정렬합니다."""
        logger.info("리뷰를 '도움순'으로 정렬합니다.")
        try:
            sort_button = await self.page.wait_for_selector(
                self.SELECTORS["sort_by_helpfulness_button"],
                timeout=5000
            )
            await sort_button.click()
            logger.info("'도움순' 정렬 버튼 클릭 성공")
            # 정렬 후 리뷰 목록이 새로고침될 때까지 대기
            # TODO: 더 안정적인 대기 방법 (e.g., network idle or a specific element change)
            await self.page.wait_for_timeout(2000)
        except Exception as e:
            logger.warning(f"'도움순'으로 정렬하는 데 실패했습니다: {e}")
            await self.page.screenshot(path="debug_screenshot_sort_fail.png")
            logger.info("디버깅 스크린샷 저장: debug_screenshot_sort_fail.png")

    async def _get_review_rating_distribution(self) -> dict[int, str]:
        """각 별점별 리뷰 분포(%)를 가져옵니다."""
        distribution = {}
        logger.info("리뷰 평점별 분포 가져오기 시작")
        try:
            graph_area_selector = "#gdasContentsArea > div > div.product_rating_area.review-write-delete > div > div.graph_area"
            await self.page.wait_for_selector(graph_area_selector, timeout=5000)

            for i in range(1, 6):  # li:nth-child(1) to li:nth-child(5)
                rating = 6 - i  # 5 stars to 1 star
                selector = f"{graph_area_selector} > ul > li:nth-child({i}) > span.per"
                percentage_text = await self._get_text(selector, timeout=1000)
                if percentage_text:
                    distribution[rating] = percentage_text
                    logger.info(f"{rating}점 리뷰 비율: {percentage_text}")
                else:
                    logger.warning(f"{rating}점 리뷰 비율을 찾을 수 없습니다.")

        except Exception as e:
            logger.warning(f"리뷰 평점별 분포를 가져오는 데 실패했습니다: {e}")
        return distribution

    async def _click_review_tab(self):
        """리뷰 탭을 클릭하여 리뷰 정보를 로드합니다."""
        try:
            review_button = await self.page.wait_for_selector(
                self.SELECTORS["review_button"],
                timeout=10000
            )
            await review_button.click()
            logger.info("리뷰 탭 클릭 성공")
            # 리뷰가 로드될 때까지 잠시 대기합니다.
            # TODO: 리뷰 컨테이너가 나타날 때까지 기다리는 더 안정적인 방법으로 변경해야 합니다.
            await self.page.wait_for_timeout(2000)
            logger.info("리뷰 정보 로딩 대기 완료")
        except Exception as e:
            logger.warning(f"리뷰 탭 클릭 실패: {e}")
            await self.page.screenshot(path="debug_screenshot_review_click_fail.png")
            logger.info("디버깅 스크린샷 저장: debug_screenshot_review_click_fail.png")

    async def _get_text(self, selector: str, timeout: int = 10000) -> str:
        """CSS selector로 요소의 텍스트를 가져옵니다."""
        element = await self.page.wait_for_selector(selector, timeout=timeout)
        text = await element.text_content()
        return text.strip() if text else ""

    async def _get_detail_images(self) -> list[str]:
        """제품 상세 이미지들을 가져옵니다."""
        # 페이지를 아래로 스크롤하여 상세정보 영역 로딩
        await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
        await self.page.wait_for_timeout(2000)

        # 상세정보 토글 버튼 클릭
        try:
            toggle_btn = await self.page.wait_for_selector(
                self.SELECTORS["detail_toggle"],
                timeout=10000
            )
            await toggle_btn.click()
            logger.info("상세정보 토글 버튼 클릭 성공")
            await self.page.wait_for_timeout(3000)  # 이미지 로딩 대기
        except Exception as e:
            logger.warning(f"상세정보 토글 버튼 클릭 실패: {e}")
            await self.page.screenshot(path="debug_screenshot.png")
            logger.info("디버깅 스크린샷 저장: debug_screenshot.png")
            return []

        # 모든 이미지 URL 수집
        images = []
        logger.info("상세 이미지 수집 시작")
        try:
            # #tempHtml2 내부의 모든 직계 div 컨테이너를 찾음
            main_container_selector = "#tempHtml2"
            await self.page.wait_for_selector(main_container_selector, timeout=5000)
            
            div_containers = await self.page.query_selector_all(f"{main_container_selector} > div")
            logger.info(f"총 {len(div_containers)}개의 상세정보 div 컨테이너 발견")

            if not div_containers:
                logger.warning("상세정보 div 컨테이너를 찾을 수 없습니다.")
                return []

            for i, div_container in enumerate(div_containers, 1):
                # 각 div 컨테이너 내의 모든 img 태그를 찾음
                imgs_in_div = await div_container.query_selector_all("img")
                logger.debug(f"Div 컨테이너 #{i}에서 {len(imgs_in_div)}개의 img 태그 발견")

                for img in imgs_in_div:
                    src = await img.get_attribute("src")
                    if not src or "http" not in src:
                        src = await img.get_attribute("data-src")
                    if not src or "http" not in src:
                        src = await img.get_attribute("data-original")

                    if src and "http" in src and src not in images:  # 유효하고 중복되지 않는 URL만 추가
                        images.append(src)
                        logger.debug(f"이미지 추가: {src}")

            if images:
                logger.info(f"총 {len(images)}개의 상세 이미지 URL 수집 완료")
            else:
                logger.warning("유효한 상세 이미지 URL을 찾을 수 없습니다")
                # 디버깅을 위해 스크린샷과 HTML 저장
                await self.page.screenshot(path="debug_screenshot_detail_img.png")
                html_content = await self.page.content()
                with open("debug_page_source_detail_img.html", "w", encoding="utf-8") as f:
                    f.write(html_content)
                logger.info("상세 이미지 디버깅 파일 저장 완료")

        except Exception as e:
            logger.error(f"상세 이미지 수집 중 오류 발생: {e}")

        return images