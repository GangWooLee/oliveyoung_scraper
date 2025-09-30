import sqlite3
from loguru import logger
from pathlib import Path

# ProductInfo 클래스의 정확한 임포트 경로를 확인해야 합니다.
# 현재 구조상으로는 아래 경로가 맞을 것으로 예상됩니다.
from src.scraper.oliveyoung_scraper import ProductInfo

DB_FILE = Path(__file__).parent.parent / "creait.db"

def init_db():
    """데이터베이스 파일을 초기화하고 테이블을 생성합니다."""
    try:
        con = sqlite3.connect(DB_FILE)
        cur = con.cursor()

        # products 테이블
        cur.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE NOT NULL,
                name TEXT,
                price TEXT,
                rating TEXT,
                review_count TEXT,
                rating_dist_5_star_percent TEXT,
                rating_dist_4_star_percent TEXT,
                rating_dist_3_star_percent TEXT,
                rating_dist_2_star_percent TEXT,
                rating_dist_1_star_percent TEXT,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # product_images 테이블
        cur.execute("""
            CREATE TABLE IF NOT EXISTS product_images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                image_url TEXT NOT NULL,
                FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE
            )
        """)

        # product_reviews 테이블
        cur.execute("""
            CREATE TABLE IF NOT EXISTS product_reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                review_text TEXT,
                FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE
            )
        """)

        con.commit()
        logger.info(f"데이터베이스 초기화 완료: {DB_FILE}")
    except Exception as e:
        logger.error(f"데이터베이스 초기화 중 오류 발생: {e}")
    finally:
        if con:
            con.close()

def save_product_info(product_info: ProductInfo, url: str):
    """스크래핑된 제품 정보를 데이터베이스에 저장합니다."""
    if not product_info or not product_info.name:
        logger.warning("저장할 제품 정보가 유효하지 않습니다.")
        return

    con = None
    try:
        con = sqlite3.connect(DB_FILE)
        cur = con.cursor()

        # 1. 제품 정보 삽입 또는 업데이트
        dist = product_info.review_rating_distribution
        
        cur.execute("SELECT id FROM products WHERE url = ?", (url,))
        result = cur.fetchone()
        if result:
            product_id = result[0]
            logger.info(f"기존 제품 발견 (ID: {product_id}). 데이터를 업데이트합니다.")
            # 기존 이미지/리뷰 삭제 (ON DELETE CASCADE로 자동 처리되지만 명시적으로도 가능)
            cur.execute("DELETE FROM product_images WHERE product_id = ?", (product_id,))
            cur.execute("DELETE FROM product_reviews WHERE product_id = ?", (product_id,))
            
            cur.execute("""
                UPDATE products 
                SET name=?, price=?, rating=?, review_count=?, 
                    rating_dist_5_star_percent=?, rating_dist_4_star_percent=?, 
                    rating_dist_3_star_percent=?, rating_dist_2_star_percent=?, 
                    rating_dist_1_star_percent=?, scraped_at=CURRENT_TIMESTAMP
                WHERE id = ?
            """, (product_info.name, product_info.price, product_info.rating, product_info.review_count,
                  dist.get(5), dist.get(4), dist.get(3), dist.get(2), dist.get(1), product_id))
        else:
            logger.info("새로운 제품을 데이터베이스에 추가합니다.")
            product_data = (
                url,
                product_info.name,
                product_info.price,
                product_info.rating,
                product_info.review_count,
                dist.get(5), dist.get(4), dist.get(3), dist.get(2), dist.get(1)
            )
            cur.execute("""
                INSERT INTO products (
                    url, name, price, rating, review_count,
                    rating_dist_5_star_percent, rating_dist_4_star_percent,
                    rating_dist_3_star_percent, rating_dist_2_star_percent,
                    rating_dist_1_star_percent
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, product_data)
            product_id = cur.lastrowid

        # 2. 상세 이미지 URL 삽입
        if product_info.detail_images:
            image_data = [(product_id, img_url) for img_url in product_info.detail_images]
            cur.executemany("INSERT INTO product_images (product_id, image_url) VALUES (?, ?)", image_data)

        # 3. 리뷰 텍스트 삽입
        if product_info.reviews:
            review_data = [(product_id, review_text) for review_text in product_info.reviews]
            cur.executemany("INSERT INTO product_reviews (product_id, review_text) VALUES (?, ?)", review_data)

        con.commit()
        logger.info(f"제품 '{product_info.name}' 정보가 데이터베이스에 성공적으로 저장되었습니다 (ID: {product_id}).")

    except Exception as e:
        logger.error(f"데이터베이스 저장 중 오류 발생: {e}")
        if con:
            con.rollback()
    finally:
        if con:
            con.close()
