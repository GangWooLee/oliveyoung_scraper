"""Creait - Instagram 광고 제품 신뢰도 분석 시스템 메인"""
import asyncio
import pprint
from loguru import logger
from src.scraper.oliveyoung_scraper import OliveYoungScraper
from src.database import init_db, save_product_info


async def main():
    """메인 실행 함수"""
    # 데이터베이스 초기화 (테이블이 없으면 생성)
    init_db()

    # 사용자로부터 URL 입력받기
    url = input("스크래핑할 올리브영 제품 URL을 입력하세요: ")
    if not url or "oliveyoung.co.kr" not in url:
        logger.warning("유효한 올리브영 URL이 아닙니다. 프로그램을 종료합니다.")
        return

    logger.info(f"입력된 URL: {url}")
    logger.info("=== Olive Young 스크래퍼 시작 ===")

    try:
        async with OliveYoungScraper(headless=True) as scraper:
            # 테스트를 위해 리뷰는 최대 30개까지만 가져옵니다.
            product = await scraper.scrape(url, max_reviews=30)

            # 결과 출력
            logger.info("\n=== 스크래핑 결과 (화면 출력) ===")
            pprint.pprint(product.__dict__)

            # 데이터베이스에 저장
            logger.info("\n=== 데이터베이스에 결과 저장 시작 ===")
            save_product_info(product, url)

    except Exception as e:
        logger.error(f"스크래핑 과정에서 오류가 발생했습니다: {e}")


if __name__ == "__main__":
    asyncio.run(main())
