import os
from datetime import datetime, timedelta
import importar_historico as ih

def build_month_str(target_month=None):
    if target_month:
        return target_month
    today = datetime.utcnow().date().replace(day=1)
    prev = today - timedelta(days=1)
    return f"{prev.year}-{prev.month:02d}"

def build_url(month_str):
    return f"https://transparenciachc.blob.core.windows.net/trnspchc/COT_{month_str}.zip"

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Importación mensual de histórico")
    parser.add_argument("--month", help="Mes a importar en formato YYYY-MM")
    parser.add_argument("--db-url", help="URL de conexión a la base de datos")
    parser.add_argument("--force", action="store_true", help="Forzar importación")
    args = parser.parse_args()

    if args.db_url:
        os.environ["DATABASE_URL"] = args.db_url
        import importlib
        importlib.reload(ih.db)

    ih.db.iniciar_db_extendida()

    month_str = build_month_str(args.month)
    url = build_url(month_str)

    conn = ih.db.get_connection()
    exists = ih.verificar_existencia(url, conn)
    conn.close()

    if exists and not args.force:
        print("Importación cancelada para evitar duplicados")
        return

    ih.descargar_y_procesar(url)

if __name__ == "__main__":
    main()
