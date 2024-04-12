import fitz
import sqlite3


# 提取PDF中的文本块，并按位置排序
def extract(page):
    text_blocks = []
    blocks = page.get_text("blocks", flags=11)
    for b in blocks:
        bbox = b[:4]
        text = b[4]
        text_blocks.append((bbox, text))
    text_blocks.sort(key=lambda x: (x[0][1], x[0][0]))
    return text_blocks


# 获取PDF中每一页的文本块的近似坐标
def coordinates(pdf_path):
    text_coordinates = {}
    with fitz.open(pdf_path) as pdf:
        for page_num in range(len(pdf)):
            page = pdf[page_num]
            text_coordinates[page_num] = extract(page)
    return text_coordinates


# 提取文本并存储到数据库
def store(chinese_pdf_path, english_pdf_path, db_name):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS TextData (
                        id INTEGER PRIMARY KEY,
                        text TEXT,
                        language TEXT,
                        page_num INTEGER,
                        block_num INTEGER,
                        x INTEGER,
                        y INTEGER
                    )''')

    chinese_text_coordinates = coordinates(chinese_pdf_path)
    english_text_coordinates = coordinates(english_pdf_path)

    for page_num in range(max(len(chinese_text_coordinates), len(english_text_coordinates))):
        chinese_blocks = chinese_text_coordinates.get(page_num, [])
        english_blocks = english_text_coordinates.get(page_num, [])

        for block_num, (chinese_block, english_block) in enumerate(zip(chinese_blocks, english_blocks), 1):
            # 对于中文文本，将多行文本合并为一个文本块
            chinese_text = "\n".join(line.strip() for line in chinese_block[1].split("\n"))
            chinese_x = int(chinese_block[0][0])
            chinese_y = int(chinese_block[0][1])
            cursor.execute("INSERT INTO TextData (text, language, page_num, block_num, x, y) VALUES (?, ?, ?, ?, ?, ?)",
                           (chinese_text, "chinese", page_num + 1, block_num, chinese_x, chinese_y))
            english_x = int(english_block[0][0])
            english_y = int(english_block[0][1])
            cursor.execute("INSERT INTO TextData (text, language, page_num, block_num, x, y) VALUES (?, ?, ?, ?, ?, ?)",
                           (english_block[1], "english", page_num + 1, block_num, english_x, english_y))

    conn.commit()
    conn.close()


chinese_pdf_path = "F:/assignment/chinese.pdf"
english_pdf_path = "F:/assignment/english.pdf"
db_name = "extract_data.db"

store(chinese_pdf_path, english_pdf_path, db_name)
