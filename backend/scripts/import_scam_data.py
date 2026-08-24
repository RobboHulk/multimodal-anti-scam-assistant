
import json
import os
import traceback

def escape_sql(val):
    if val is None:
        return "NULL"
    return "'" + str(val).replace("'", "''").replace("\\", "\\\\") + "'"

def map_scam_type(title, content):
    text = (title + content).lower()
    if any(k in text for k in ["理财", "投资", "收益", "理财专家"]):
        return "INVESTMENT_SCAM"
    if any(k in text for k in ["警察", "公安", "公检法", "法院", "检察院", "反诈中心", "国家反诈中心"]):
        return "IMPERSONATE_GOV"
    if any(k in text for k in ["熟人", "领导", "朋友", "亲戚", "转账"]):
        return "IMPERSONATE_FRIEND"
    if any(k in text for k in ["客服", "淘宝", "京东", "拼多多", "退款", "售后"]):
        return "IMPERSONATE_SERVICE"
    if any(k in text for k in ["贷款", "秒到", "高利贷", "低息"]):
        return "LOAN_SCAM"
    if any(k in text for k in ["刷单", "兼职", "返利", "日赚"]):
        return "BRUSHING_SCAM"
    if any(k in text for k in ["游戏", "装备", "充值", "点券"]):
        return "GAMING_SCAM"
    if any(k in text for k in ["杀猪盘", "裸聊", "情感", "网恋"]):
        return "EMOTIONAL_SCAM"
    return "OTHER_SCAM"

def run_import():
    try:
        # Base directory for the project (assuming backend/scripts/)
        curr_dir = os.path.dirname(os.path.abspath(__file__))
        base_dir = os.path.dirname(os.path.dirname(curr_dir))
        data_dir = os.path.join(base_dir, "docs", "data")
        output_dir = os.path.join(base_dir, "docs", "sql")
        output_file = os.path.join(output_dir, "import_competition_data.sql")

        print(f"Data Dir: {data_dir}")
        print(f"Output File: {output_file}")

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        json_files = [
            "百度反诈.json",
            "搜狗反诈.json",
            "搜狗-诈骗套路.json",
            "搜狗诈骗预警.json"
        ]

        sql_statements = []
        sql_statements.append("SET NAMES utf8mb4;")
        sql_statements.append("USE anti_scam;")
        sql_statements.append("TRUNCATE TABLE knowledge_article;")

        found_any = False
        for filename in json_files:
            filepath = os.path.join(data_dir, filename)
            if not os.path.exists(filepath):
                print(f"Skipping {filename} (not found)")
                continue
            
            found_any = True
            print(f"Processing {filename}...")
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                source_url = data.get("source_url", "")
                website_name = data.get("website_name", "")
                articles = data.get("source_data", [])
                
                for art in articles:
                    title = art.get("title", "")
                    content = art.get("content", "")
                    if not title or not content:
                        continue
                    
                    scam_type = map_scam_type(title, content)
                    tags = scam_type.replace("_", " ").lower()
                    
                    stmt = f"INSERT INTO knowledge_article (title, scam_type, content, tags, source, source_url, status) VALUES ({escape_sql(title)}, {escape_sql(scam_type)}, {escape_sql(content)}, {escape_sql(tags)}, {escape_sql(website_name)}, {escape_sql(source_url)}, 1);"
                    sql_statements.append(stmt)
        
        if not found_any:
            print("No JSON files found in data directory!")
            return

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(sql_statements))

        print(f"Success! Generated {len(sql_statements)-3} insert statements.")
        print(f"SQL file saved to: {output_file}")

    except Exception:
        print("An error occurred during execution:")
        traceback.print_exc()

if __name__ == "__main__":
    run_import()
