Day1–2（Next.js：雛形→Tailwind→shadcn→/login）

ゴール：http://localhost:3000/login が開いてフォームが出る（ダミーでOK）。

プロンプト（そのままCursorへ）

プロジェクト名は frontend。Next.js 14（TS）で新規作成し、Tailwind と shadcn/ui を導入して、/login ページ（メール・パスワード・ログインボタンのモック）を実装して。

npx create-next-app@latest frontend --ts --eslint で作成

Tailwind: npm i -D tailwindcss postcss autoprefixer && npx tailwindcss init -p

tailwind.config.js の content に ./src/pages/**/*, ./src/components/**/*, ./src/app/**/* を設定、src/app/globals.css に @tailwind base; @tailwind components; @tailwind utilities; を追加

npx shadcn-ui@latest init → npx shadcn-ui@latest add button input label

src/app/layout.tsx に共通ヘッダ/フッタ（Home/Loginリンク）を追加

src/app/login/page.tsx を作成し、shadcnの Input/Label/Button でフォームを実装（onSubmit は preventDefault でOK）

npm run dev で起動し、/login が表示されることを確認
Done基準：/login が表示・入力できる

Day3–4（FastAPI：雛形→/health→CORS→ログ）

ゴール：http://127.0.0.1:8000/health が {"status":"ok"} を返す。

プロンプト

backend ディレクトリを新規に作って、FastAPI の最小アプリを構築して。
要件：

python -m venv .venv → 有効化 → pip install fastapi uvicorn[standard] pydantic

main.py に FastAPI() を作り、GET /health で {"status":"ok"} を返す

CORS：allow_origins=["http://localhost:3000"] で GET/POST 等を許可

標準の logging でアクセス/アプリログをINFO出力

起動コマンドは uvicorn main:app --reload --port 8000
Done基準：ブラウザ/curl で /health がOK、CORSも許可されている

Day5–6（DB：SQLite→SQLAlchemy→Alembic）

ゴール：Pythonコードから users に INSERT/SELECT できる。

プロンプト

FastAPIに SQLite + SQLAlchemy + Alembic を導入して“最小ユーザー登録”を実装して。
前提：開発DBはSQLite（本番は後日Postgres/RDSへ移行）。
要件：

依存：pip install sqlalchemy aiosqlite alembic passlib[bcrypt] python-dotenv

.env に DATABASE_URL=sqlite+aiosqlite:///./dev.db

SQLAlchemyモデル：User(id PK, email unique, password_hash, created_at)

起動時に Base.metadata.create_all() でテーブル作成（将来に備えて Alembic も alembic init だけ実施）

POST /users：{email, password} を受け取り bcrypt でハッシュ化してINSERT、GET /users で一覧取得

例外時は 400/409 を返却（メール重複など）
Done基準：/users に対して INSERT/SELECT が動く（ログにSQL/件数が出る）

Day7（つなぎ：FE→BE→DB）

ゴール：「Next.js /login 画面からボタンで FastAPI を叩き、バックエンドでDBへ触れる最小ループ」を確認する。

プロンプト

Next.js から FastAPI を呼ぶ“配線”を作って、最小の通し動作を確認したい。
要件：

frontend に NEXT_PUBLIC_API_BASE=http://127.0.0.1:8000 を追加（.env.local）

src/app/api/ping/route.ts（任意）から fetch(\${process.env.NEXT_PUBLIC_API_BASE}/health`)を叩くサンプルを置く or 直接loginページのボタンonClickで/healthをfetch`

追加で、/users にテスト登録するボタンを用意（固定メールで1回だけ成功、重複時はエラーをトースト表示）

画面にAPIレスポンス（status や登録結果）を表示
Done基準：フロント→API→DB の一連がローカルで通る