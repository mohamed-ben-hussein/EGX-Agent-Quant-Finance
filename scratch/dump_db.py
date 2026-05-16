import sqlite3
import sys

def dump_db():
    conn = sqlite3.connect('data/egx.db')
    cursor = conn.execute("SELECT id, title, article_url, pdf_path FROM disclosures")
    print(f"{'ID':<5} | {'Title Snippet':<30} | {'PDF'}")
    print("-" * 80)
    for row in cursor:
        title = row[1] if row[1] else "No Title"
        # Print with replacement for console issues
        safe_title = title[:27].encode(sys.stdout.encoding, errors='replace').decode(sys.stdout.encoding)
        has_pdf = "YES" if row[3] else "NO"
        print(f"{row[0]:<5} | {safe_title:<30} | {has_pdf} | {row[2]}")
    conn.close()

if __name__ == "__main__":
    dump_db()
