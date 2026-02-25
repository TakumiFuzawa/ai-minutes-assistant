import os
import shutil
from datetime import datetime
# FastAPI関連を1行に集約
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Request, Path
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates 
from dotenv import load_dotenv
from openai import OpenAI  
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime 
from sqlalchemy.ext.declarative import declarative_base 
from sqlalchemy.orm import sessionmaker, Session

# .env ファイルを読み込む
load_dotenv()
# OpenAIクライアントの初期化
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# --- データベース設定 (SQLAlchemy) ---
DATABASE_URL = "sqlite:///./minutes.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# DBのテーブル構造（モデル）を定義
class Minute(Base):
    __tablename__ = "minutes"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    raw_text = Column(Text)
    summary = Column(Text)
    created_at = Column(DateTime, default=datetime.now)

# 実際にDBファイルとテーブルを作成
Base.metadata.create_all(bind=engine)

# DBセッションを取得するための関数
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
# ------------------------------------

app = FastAPI()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# テンプレートエンジンの準備
templates = Jinja2Templates(directory="templates")  

@app.get("/")
async def main(request: Request, db: Session = Depends(get_db)): 
    minutes = db.query(Minute).order_by(Minute.created_at.desc()).all()
    # 1. DBから過去の議事録をすべて取得（作成日時の降順）
    minutes = db.query(Minute).order_by(Minute.created_at.desc()).all()
    # HTMLファイルを読み込んでデータを流し込む（これがプロのやり方！）
    return templates.TemplateResponse("index.html", {"request": request, "minutes": minutes})

@app.post("/upload")
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)): # db引数を追加
    file_location = os.path.join(UPLOAD_DIR, file.filename)
    file_location = os.path.join(UPLOAD_DIR, file.filename)
    
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        # 1. Whisper APIで文字起こし
        with open(file_location, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file
            )
        
        raw_text = transcript.text

        # 2. GPT-4oで議事録を要約
        # エンジニアの腕の見せ所「プロンプトエンジニアリング」です
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "あなたは優秀な秘書です。提供された音声文字起こしから、簡潔で分かりやすい議事録を作成してください。"},
                {"role": "user", "content": (
                    f"以下のテキストを【議題】【決定事項】【TODO】の形式でまとめてください。\n"
                    f"特に【TODO】は、後でチェックリストとして使えるように、必ず「- [ ] 」から始まる形式で箇条書きにしてください。\n\n"
                    f"テキスト：\n{raw_text}"
                )}
            ]
        )
        
        summary = response.choices[0].message.content

        # 3. DBに保存
        new_minute = Minute(
            filename=file.filename,
            raw_text=raw_text,
            summary=summary
        )
        db.add(new_minute)
        db.commit() # 確定  
        db.refresh(new_minute) # 保存後のデータを反映

        # 3. 両方の結果を返す
        return {
            "filename": file.filename,
            "raw_text": raw_text,
            "summary": summary,
            "id": new_minute.id # 保存されたデータのIDを返す
        }
        
    except Exception as e:
        db.rollback() # エラー時はやり直す
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(file_location):
            os.remove(file_location)

@app.delete("/delete/{minute_id}")
async def delete_minute(minute_id: int, db: Session = Depends(get_db)):
    import os
    # 1. まずデータがあるか確認
    target = db.query(Minute).filter(Minute.id == minute_id).first()
    
    if not target:
        raise HTTPException(status_code=404, detail="データが見つかりませんでした")

    try:
        # 2. 実ファイルの削除（失敗してもDB削除は進めるように try-except を個別に設定）
        if target.filename:
            file_full_path = os.path.join("uploads", target.filename)
            if os.path.exists(file_full_path):
                os.remove(file_full_path)

        # 3. DBからレコードを削除（ここが重要！）
        db.delete(target)
        db.commit()  # ここで初めてDBに「消して確定！」と命令が飛びます
        
        return {"message": "議事録とファイルを完全に削除しました"}

    except Exception as e:
        db.rollback() # エラーが起きたら処理を巻き戻す
        print(f"削除中にエラー発生: {e}")
        raise HTTPException(status_code=500, detail=f"内部エラー: {str(e)}")