import os
from datetime import datetime, date, timedelta
from os import getenv

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from model import MLModel


def cleanup():
    load_dotenv()
    db_engine = create_engine(getenv('DATABASE_URL'))
    Session = sessionmaker(bind=db_engine)
    session = Session()

    inactive_models = session.query(MLModel).filter(MLModel.active == False, MLModel.file_name != None).all()
    remove_files(inactive_models)

    today = date.today()
    previous_sunday = today - timedelta(today.weekday())
    print(f'deleting files for active models older than {previous_sunday}')
    old_models = session.query(MLModel).filter(MLModel.active == True,
                                               MLModel.created_at < datetime.combine(previous_sunday,
                                                                                     datetime.min.time()),
                                               MLModel.file_name != None).all()
    remove_files(old_models)

    session.commit()
    session.close()


def remove_files(models):
    print(f'attempting to delete {len(models)} model files')
    for model in models:
        file = model.file_name
        if file is not None and os.path.exists(file):
            os.remove(file)
        else:
            print(f'file: {file} not found. cannot remove')
        model.file_name = None
        model.active = False


if __name__ == '__main__':
    cleanup()
