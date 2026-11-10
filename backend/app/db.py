from collections.abc import Generator
from pathlib import Path

from sqlmodel import Session, SQLModel, create_engine
                                               
from app.config import get_settings

settings = get_settings()
database_url = settings.resolved_database_url

connect_args: dict[str, object] = {}                         
if database_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False
                                                                              
                                            
engine = create_engine(database_url, connect_args=connect_args, echo=False)
                                       

def _migrate_review_columns() -> None:
    """Lightweight SQLite migration for review analysis columns.

    Production deployments should use Alembic; this demo uses idempotent
    ALTER TABLE statements instead.
    """
    if not database_url.startswith("sqlite"):
        return

    additions = {
        "user_id": "TEXT",
        "order_id": "TEXT",
        "sentiment": "TEXT DEFAULT 'neutral'",
        "summary": "TEXT DEFAULT ''",
        "pros": "JSON DEFAULT '[]'",
        "cons": "JSON DEFAULT '[]'",
        "tags": "JSON DEFAULT '[]'",
        "created_at": "DATETIME",
        "updated_at": "DATETIME",
    }

    with engine.begin() as connection:
        columns = {
            row[1]
            for row in connection.exec_driver_sql(
                "PRAGMA table_info(reviews)"
            ).fetchall()
        }
        for name, ddl in additions.items():
            if name not in columns:
                connection.exec_driver_sql(
                    f"ALTER TABLE reviews ADD COLUMN {name} {ddl}"
                )

        connection.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS ix_reviews_user_id ON reviews (user_id)"
        )
        connection.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS ix_reviews_order_id ON reviews (order_id)"
        )

                                                       
        connection.exec_driver_sql(
            "UPDATE reviews SET sentiment = CASE "
            "WHEN rating >= 4 THEN 'positive' "
            "WHEN rating = 3 THEN 'neutral' "
            "ELSE 'negative' END "
            "WHERE user_id IS NULL AND order_id IS NULL "
            "AND sentiment = 'neutral' AND (summary IS NULL OR summary = '')"
        )
        connection.exec_driver_sql(
            "UPDATE reviews SET summary = substr(content, 1, 60) "
            "WHERE user_id IS NULL AND order_id IS NULL "
            "AND (summary IS NULL OR summary = '') AND content <> ''"
        )
        connection.exec_driver_sql(
            "UPDATE reviews SET created_at = CURRENT_TIMESTAMP "
            "WHERE created_at IS NULL"
        )
        connection.exec_driver_sql(
            "UPDATE reviews SET updated_at = COALESCE(created_at, CURRENT_TIMESTAMP) "
            "WHERE updated_at IS NULL"
        )


def init_db() -> None:
    """Create tables and make sure the SQLite parent directory exists."""
    if database_url.startswith("sqlite:///"):
        db_path = Path(database_url.removeprefix("sqlite:///"))                            
        db_path.parent.mkdir(parents=True, exist_ok=True)                   
                                                
                                                                         
    from app import models              

    SQLModel.metadata.create_all(engine)
    _migrate_review_columns()
                                        
                         
                                       
def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
                                                     
                                                         
                                             
                                                                                                                                 
                 
                       
         
                
                             
              
                   
                                        
    
         
                                 
                                
                                      
                                                                                              