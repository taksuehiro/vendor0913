Day6：FastAPIを新規作成（完全いちから）

ゴール：GET /health が {"status":"ok"}（CORS許可済み）

Cursorプロンプト（そのまま貼ってOK）

新規に backend/ を作り、FastAPIの最小構成を作って。
要件：

venv作成＆依存導入：fastapi, uvicorn[standard], pydantic

main.py に FastAPI() を作成し、GET /health で {"status":"ok"} を返す

CORSは allow_origins=["http://localhost:3000"]、methods/headersは*で許可

ロギング（INFO）を設定

起動コマンド：uvicorn main:app --reload --port 8000
期待物：backend/README.md に起動手順・依存一覧・確認URLを記載

チェック

uvicorn 起動 → http://127.0.0.1:8000/health でOK

CORSエラーが出ない（後でFEから叩く）

Day7：DB（SQLite）＋ /auth/register /auth/verify

ゴール：NextAuth側のauthorize()から叩ける認証APIが生える

Cursorプロンプト

FastAPIに**SQLite + SQLAlchemy + Alembic + passlib[bcrypt]**を導入し、認証APIを追加して。
要件：

依存：sqlalchemy, aiosqlite, alembic, passlib[bcrypt], python-dotenv

.env に DATABASE_URL=sqlite+aiosqlite:///./dev.db

モデル：User(id PK, email unique, password_hash, created_at)

起動時に Base.metadata.create_all()（Alembicはinitだけ実施、将来用）

POST /auth/register {email, password}：bcryptで保存（開発用）

POST /auth/verify {email, password}：一致すれば{id,email,org_id:1} を返し、失敗は401

バリデーション/重複時は400/409

単体テスト（pytest）でregister→verifyのハッピー/アンハッピーを各1本
期待物：models.py, schema.py, auth.py 分離、backend/README.md更新

チェック

curl -X POST /auth/register → 201

curl -X POST /auth/verify → 200/401 を返し分け

Day8：JWT共有（NextAuthと同じシークレットで検証）

ゴール：保護APIでAuthorization: Bearer <JWT>を検証し、user_id/org_idを取得

Cursorプロンプト

フロントのNextAuthで発行されるJWT（HS256, NEXTAUTH_SECRET）をFastAPIでも検証できるよう実装して。
要件：

依存：python-jose[cryptography]

環境変数：NEXTAUTH_SECRET を .env に追加（開発値でOK）

security.py に get_current_user()（依存）を実装：

Authorization: Bearer <token> を受け取り、HS256で検証

成功時に {user_id, org_id} を返す、失敗は401

テスト用に GET /me を追加（上記依存で守る）

例外ハンドラで401時に統一レスポンス
期待物：security.py, routers/me.py など、モジュール分割とREADMEの追記

チェック

ダミーの有効JWTで /me→200、壊したトークンで→401

Day9：RAG最小（ローカル版・Chroma）

ゴール：Markdown群から引用付きで答える関数をFastAPIに組込み

Cursorプロンプト

LangChainで最小RAG（ローカルChroma版）を実装し、POST /search で回答＋引用を返して。
要件：

依存：langchain, langchain-openai, chromadb（またはlangchain-community同等）

インジェスト：Markdownを読み込み→MarkdownHeaderTextSplitter/RecursiveCharacterTextSplitterで分割（1,000–1,500字、overlap 100–200）

埋め込み：OpenAIEmbeddings、VectorStoreはChroma（ローカル）

検索：k指定、MMRのon/off切替可能、スコア閾値未満なら「わからない」

生成：ChatOpenAIで回答、必ず引用（title,url,page）を含めるプロンプト

API：POST /search {query, k, mmr} → {answer, citations:[{title,url,score}]}

設定：OpenAIキーは .env、将来pgvectorへ差し替え可能な抽象レイヤーvector_port.pyを作る
期待物：rag/ingest.py, rag/search.py, rag/vector_port.py, routers/search.py とREADME追記

チェック

ローカルのサンプルmd数本で /search → 200 & 引用が最低1件

スコア低い時は「わからない」方針で返る

Day10：Next.jsから /search を叩く（UI配線）

ゴール：/dashboard/search からフォーム送信→回答＋引用カード表示

Cursorプロンプト

フロント（Next.js）に検索画面を追加し、FastAPIの/searchを叩いて結果を表示して。
要件：

.env.local に NEXT_PUBLIC_API_BASE=http://127.0.0.1:8000

画面：/dashboard/search に検索フォーム（query, k, mmr）

送信時に POST ${API_BASE}/search を呼び、answer と citations（タイトル/URL/スコア）をカードで一覧表示

ローディング/エラー/空結果の分岐、shadcnのSkeleton/Toast利用

401/403なら/loginへリダイレクト（保護APIを想定）

コードはApp Router準拠（Server Component + Client Componentの棲み分け）
期待物：src/app/dashboard/search/page.tsx、フェッチの小さなラッパ、UX用コンポーネント

チェック

画面から任意のクエリ→回答＋引用が数秒で表示

k/MMR切替が効く

仕上げメモ（環境・動かし方の定型）

フロント

npm run dev（http://localhost:3000）

.env.local：NEXT_PUBLIC_API_BASE, NEXTAUTH_SECRET（ダミーでOK）

バック

uvicorn main:app --reload --port 8000

.env：DATABASE_URL, OPENAI_API_KEY, NEXTAUTH_SECRET

通し動作の確認

POST /auth/register → POST /auth/verify が200

/dashboard/search で送信 → /search が回答＋引用を返す