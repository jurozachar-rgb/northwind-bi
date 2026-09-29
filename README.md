# Northwind BI – mini dashboard

Jednoduchý BI nástroj v Pythone (Streamlit + Plotly) nad ukážkovou databázou **Northwind** v PostgreSQL (Supabase).

Obsahuje KPI (tržby, objednávky, zákazníci, priemerná objednávka), tržby po mesiacoch, top 10 produktov, tržby podľa kategórie, mapu tržieb podľa krajín a tabuľku top zákazníkov s exportom do CSV. Filtrovať sa dá podľa rokov a krajín.

## 1. Databáza na Supabase (zadarmo)

1. Zaregistruj sa na [supabase.com](https://supabase.com) a vytvor nový projekt (región napr. Frankfurt). Heslo k databáze si ulož.
2. Stiahni `northwind.sql` z repozitára [pthom/northwind_psql](https://github.com/pthom/northwind_psql).
3. V Supabase otvor **SQL Editor**, vlož obsah súboru a spusti ho. Ak je editor pomalý, použi `psql` (viď nižšie).
4. Over si: `SELECT count(*) FROM orders;` → má vrátiť **830**.
5. Klikni na **Connect** a skopíruj URI pre **Session pooler** (funguje aj cez IPv4):
   ```
   postgresql://postgres.XXXX:HESLO@aws-0-eu-central-1.pooler.supabase.com:5432/postgres
   ```

Alternatíva cez terminál:
```bash
psql "TVOJ_CONNECTION_STRING" -f northwind.sql
```

## 2. Spustenie lokálne

```bash
pip install -r requirements.txt
mkdir -p .streamlit
echo 'DATABASE_URL = "postgresql://postgres.XXXX:HESLO@...:5432/postgres"' > .streamlit/secrets.toml
streamlit run app.py
```

Dashboard sa otvorí na http://localhost:8501.

> `.streamlit/secrets.toml` pridaj do `.gitignore`, heslo nepatrí na GitHub.

## 3. Zverejnenie zadarmo (Streamlit Community Cloud)

1. Nahraj `app.py`, `requirements.txt` a `README.md` do nového repozitára na GitHube.
2. Na [share.streamlit.io](https://share.streamlit.io) sa prihlás cez GitHub a daj **Create app**, vyber repozitár a `app.py`.
3. V **Advanced settings → Secrets** vlož riadok `DATABASE_URL = "..."`.
4. Dostaneš verejnú adresu typu `nazov.streamlit.app`.

## Čo skúsiť ďalej (na učenie)

- Pridať porovnanie rok k roku (YoY) do KPI cez `st.metric(..., delta=...)`.
- Stránku „Zamestnanci“: tržby podľa obchodníka (tabuľka `employees`).
- Analýzu dopravcov: priemerný čas doručenia (`shipped_date - order_date`) podľa `shippers`.
- Vytvoriť v databáze `VIEW` so spoločným základom dopytu namiesto skladania SQL v Pythone.
