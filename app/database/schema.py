from sqlalchemy import inspect, text
from app.database.connection import engine


def get_schema_info() -> str:
    inspector = inspect(engine)
    schema_parts = []

    for table_name in inspector.get_table_names():
        columns = inspector.get_columns(table_name)
        pk = inspector.get_pk_constraint(table_name)
        fks = inspector.get_foreign_keys(table_name)
        indexes = inspector.get_indexes(table_name)

        col_defs = []
        for col in columns:
            col_type = str(col["type"])
            nullable = "NULLABLE" if col["nullable"] else "NOT NULL"
            col_defs.append(f"    {col['name']} {col_type} {nullable}")

        pk_cols = ", ".join(pk["constrained_columns"]) if pk["constrained_columns"] else "None"
        fk_lines = []
        for fk in fks:
            referred_table = fk["referred_table"]
            constrained = ", ".join(fk["constrained_columns"])
            referred_cols = ", ".join(fk["referred_columns"])
            fk_lines.append(f"    FOREIGN KEY ({constrained}) REFERENCES {referred_table}({referred_cols})")

        idx_lines = []
        for idx in indexes:
            idx_cols = ", ".join(idx["column_names"])
            unique = "UNIQUE " if idx["unique"] else ""
            idx_lines.append(f"    {unique}INDEX ({idx_cols})")

        table_str = f"TABLE {table_name} (\n"
        table_str += ",\n".join(col_defs)
        if fk_lines:
            table_str += ",\n" + ",\n".join(fk_lines)
        if idx_lines:
            table_str += ",\n" + ",\n".join(idx_lines)
        table_str += f"\n) PRIMARY KEY ({pk_cols})"

        schema_parts.append(table_str)

    return "\n\n".join(schema_parts)


def get_table_names() -> list[str]:
    inspector = inspect(engine)
    return inspector.get_table_names()


def get_table_details(table_name: str) -> dict:
    inspector = inspect(engine)
    columns = inspector.get_columns(table_name)
    pk = inspector.get_pk_constraint(table_name)
    fks = inspector.get_foreign_keys(table_name)

    return {
        "columns": [
            {"name": c["name"], "type": str(c["type"]), "nullable": c["nullable"]}
            for c in columns
        ],
        "primary_key": pk["constrained_columns"],
        "foreign_keys": fks,
    }


def get_sample_rows(table_name: str, limit: int = 3) -> list[dict]:
    with engine.connect() as conn:
        result = conn.execute(text(f"SELECT * FROM {table_name} LIMIT :limit"), {"limit": limit})
        columns = list(result.keys())
        return [dict(zip(columns, row)) for row in result.fetchall()]
