# Creait - 올리브영 제품 리뷰 스크레이퍼

올리브영 (Olive Young) 웹사이트의 제품 페이지에서 상세 정보, 이미지, 사용자 리뷰를 수집하는 파이썬 기반 웹 스크레이퍼입니다. 수집된 데이터는 SQLite 데이터베이스에 저장되어 데이터 분석에 활용될 수 있습니다.

## 주요 기능

- **상세 정보 수집**: 제품명, 가격, 종합 평점, 전체 리뷰 수를 수집합니다.
- **리뷰 평점 분포**: 5점부터 1점까지 각 별점의 리뷰가 몇 퍼센트를 차지하는지 수집합니다.
- **상세 이미지 추출**: 제품 상세 설명에 포함된 모든 이미지를 추출합니다.
- **리뷰 수집**: '도움순'으로 리뷰를 정렬한 후, 지정된 개수만큼의 리뷰 텍스트를 수집합니다.
- **자동 페이지네이션**: 리뷰 페이지를 자동으로 넘기며 데이터를 수집합니다.
- **데이터베이스 저장**: 수집된 모든 정보를 `creait.db` SQLite 데이터베이스 파일에 저장 및 업데이트합니다.
- **데이터프레임 변환 예제**: 저장된 데이터를 `pandas` 데이터프레임으로 불러와 활용하는 예제를 제공합니다.

## 기술 스택

- **웹 스크래핑**: Playwright
- **데이터베이스**: sqlite3 (Python 내장)
- **로깅**: Loguru
- **데이터 분석 (예제)**: pandas
- **패키지 관리**: uv

## 프로젝트 구조

```
creait/
├── src/
│   ├── scraper/
│   │   └── oliveyoung_scraper.py  # 올리브영 스크레이퍼 클래스
│   ├── __init__.py
│   └── database.py              # 데이터베이스 초기화 및 저장 로직
├── main.py                      # 메인 실행 스크립트
├── db_to_dataframe_ex.py        # DB를 DataFrame으로 변환하는 예제
├── pyproject.toml               # 프로젝트 의존성 관리
├── uv.lock                      # uv 잠금 파일
├── .env.example
└── README.md
```

## 설치 및 실행

### 1. 환경 설정

```bash
# 의존성 설치 (uv 사용)
# uv가 설치되어 있지 않다면: pip install uv
uv pip sync

# Playwright 브라우저 드라이버 설치
uv run playwright install --with-deps chromium
```

### 2. 스크레이퍼 실행

아래 명령어를 실행하면 스크래핑할 올리브영 제품 URL을 입력하라는 프롬프트가 나타납니다.

```bash
python main.py
```

URL을 입력하고 엔터를 누르면 스크래핑이 시작되고, 완료 후 결과가 화면에 출력된 뒤 `creait.db` 파일에 저장됩니다.

### 3. 수집된 데이터 확인

`db_to_dataframe_ex.py` 스크립트를 실행하여 데이터베이스에 저장된 `products` 테이블의 내용을 pandas 데이터프레임으로 확인할 수 있습니다.

```bash
# pandas가 설치되어 있지 않다면: uv pip install pandas
python db_to_dataframe_ex.py
```

## 데이터베이스 스키마

### `products` 테이블
- `id`: 제품 고유 ID
- `url`: 제품 페이지 URL
- `name`: 제품명
- `price`: 가격
- `rating`: 종합 평점
- `review_count`: 총 리뷰 수
- `rating_dist_5_star_percent` ~ `rating_dist_1_star_percent`: 별점별 리뷰 비율
- `scraped_at`: 수집 시각

### `product_images` 테이블
- `id`: 이미지 고유 ID
- `product_id`: `products` 테이블의 ID (FK)
- `image_url`: 이미지 URL

### `product_reviews` 테이블
- `id`: 리뷰 고유 ID
- `product_id`: `products` 테이블의 ID (FK)
- `review_text`: 리뷰 내용
