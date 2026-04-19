import pandas as pd
import chardet
from app import app, db
from models import Study, Sample

def detect_encoding(file_path):
    """Автоматическое определение кодировки файла"""
    with open(file_path, 'rb') as f:
        raw_data = f.read(100000)  # Читаем первые 100KB для определения
        result = chardet.detect(raw_data)
        return result['encoding']

def init_database():
    with app.app_context():
        # Удаляем старые таблицы и создаем новые
        db.drop_all()
        db.create_all()
        
        print("Загрузка данных из CSV...")
        
        # Определяем кодировку
        encoding = detect_encoding('BioTIMEMetadata_24_06_2021.csv')
        print(f"Определена кодировка: {encoding}")
        
        # Загружаем CSV с правильной кодировкой
        try:
            df = pd.read_csv('BioTIMEMetadata_24_06_2021.csv', encoding=encoding)
        except:
            # Если не получилось, пробуем другие распространенные кодировки
            for enc in ['utf-8', 'latin1', 'cp1251', 'iso-8859-1', 'cp1252']:
                try:
                    df = pd.read_csv('BioTIMEMetadata_24_06_2021.csv', encoding=enc)
                    print(f"Успешно загружено с кодировкой: {enc}")
                    break
                except:
                    continue
            else:
                raise Exception("Не удалось загрузить файл ни с одной из кодировок")
        
        # Очистка данных
        df = df.fillna(0)
        
        # Преобразование PROTECTED_AREA (может быть TRUE/True/true/1)
        df['PROTECTED_AREA'] = df['PROTECTED_AREA'].astype(str).str.upper().str.strip()
        df['PROTECTED_AREA'] = df['PROTECTED_AREA'].isin(['TRUE', '1', 'YES', 'Y'])
        
        # Приводим числовые поля к корректным типам
        numeric_fields = ['STUDY_ID', 'DATA_POINTS', 'START_YEAR', 'END_YEAR', 
                         'NUMBER_OF_SPECIES', 'NUMBER_OF_SAMPLES']
        for field in numeric_fields:
            df[field] = pd.to_numeric(df[field], errors='coerce').fillna(0).astype(int)
        
        float_fields = ['CENT_LAT', 'CENT_LONG', 'GRAIN_SQ_KM', 'AREA_SQ_KM']
        for field in float_fields:
            df[field] = pd.to_numeric(df[field], errors='coerce').fillna(0.0).astype(float)
        
        studies_added = 0
        
        for _, row in df.iterrows():
            try:
                study = Study(
                    study_id=int(row['STUDY_ID']) if pd.notna(row['STUDY_ID']) and row['STUDY_ID'] != 0 else 0,
                    realm=str(row['REALM'])[:50] if pd.notna(row['REALM']) and str(row['REALM']) != '0' else '',
                    climate=str(row['CLIMATE'])[:50] if pd.notna(row['CLIMATE']) and str(row['CLIMATE']) != '0' else '',
                    habitat=str(row['HABITAT'])[:100] if pd.notna(row['HABITAT']) and str(row['HABITAT']) != '0' else '',
                    protected_area=bool(row['PROTECTED_AREA']),
                    biome_map=str(row['BIOME_MAP'])[:150] if pd.notna(row['BIOME_MAP']) and str(row['BIOME_MAP']) != '0' else '',
                    taxa=str(row['TAXA'])[:150] if pd.notna(row['TAXA']) and str(row['TAXA']) != '0' else '',
                    organisms=str(row['ORGANISMS'])[:200] if pd.notna(row['ORGANISMS']) and str(row['ORGANISMS']) != '0' else '',
                    title=str(row['TITLE'])[:500] if pd.notna(row['TITLE']) and str(row['TITLE']) != '0' else '',
                    has_plot=str(row['HAS_PLOT'])[:1] if pd.notna(row['HAS_PLOT']) and str(row['HAS_PLOT']) != '0' else '',
                    data_points=int(row['DATA_POINTS']) if pd.notna(row['DATA_POINTS']) and row['DATA_POINTS'] > 0 else 0,
                    start_year=int(row['START_YEAR']) if pd.notna(row['START_YEAR']) and row['START_YEAR'] > 0 else 0,
                    end_year=int(row['END_YEAR']) if pd.notna(row['END_YEAR']) and row['END_YEAR'] > 0 else 0,
                    cent_lat=float(row['CENT_LAT']) if pd.notna(row['CENT_LAT']) and row['CENT_LAT'] != 0 else 0.0,
                    cent_long=float(row['CENT_LONG']) if pd.notna(row['CENT_LONG']) and row['CENT_LONG'] != 0 else 0.0,
                    number_of_species=int(row['NUMBER_OF_SPECIES']) if pd.notna(row['NUMBER_OF_SPECIES']) and row['NUMBER_OF_SPECIES'] > 0 else 0,
                    number_of_samples=int(row['NUMBER_OF_SAMPLES']) if pd.notna(row['NUMBER_OF_SAMPLES']) and row['NUMBER_OF_SAMPLES'] > 0 else 0,
                    grain_sq_km=float(row['GRAIN_SQ_KM']) if pd.notna(row['GRAIN_SQ_KM']) and row['GRAIN_SQ_KM'] != 0 else 0.0,
                    area_sq_km=float(row['AREA_SQ_KM']) if pd.notna(row['AREA_SQ_KM']) and row['AREA_SQ_KM'] != 0 else 0.0,
                    abundance_type=str(row['ABUNDANCE_TYPE'])[:50] if pd.notna(row['ABUNDANCE_TYPE']) and str(row['ABUNDANCE_TYPE']) != '0' else '',
                    biomass_type=str(row['BIOMASS_TYPE'])[:50] if pd.notna(row['BIOMASS_TYPE']) and str(row['BIOMASS_TYPE']) != '0' else '',
                    web_link=str(row['WEB_LINK'])[:500] if pd.notna(row['WEB_LINK']) and str(row['WEB_LINK']) != '0' else '',
                    license=str(row['LICENSE'])[:50] if pd.notna(row['LICENSE']) and str(row['LICENSE']) != '0' else ''
                )
                db.session.add(study)
                studies_added += 1
                
                # Добавляем демо-образец для каждого исследования
                sample = Sample(
                    study=study,
                    sample_name=f"Sample_{row['STUDY_ID']}",
                    year=study.start_year if study.start_year > 0 else 2000,
                    month=6,
                    day=15,
                    abundance=float(row['DATA_POINTS']) if row['DATA_POINTS'] > 0 else 100.0,
                    biomass=0.0,
                    sample_desc=f"Example sample from {study.title[:50] if study.title else 'Unknown'}"
                )
                db.session.add(sample)
                
                # Коммитим каждые 100 записей для экономии памяти
                if studies_added % 100 == 0:
                    db.session.commit()
                    print(f"Загружено {studies_added} исследований...")
                    
            except Exception as e:
                print(f"Ошибка при загрузке записи {_}: {e}")
                continue
        
        db.session.commit()
        print(f"\n✅ Загружено {studies_added} исследований и {studies_added} демо-образцов")
        print("✅ База данных успешно создана!")

if __name__ == '__main__':
    # Устанавливаем chardet, если его нет
    try:
        import chardet
    except ImportError:
        import subprocess
        import sys
        print("Установка chardet...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "chardet"])
        import chardet
    
    init_database()
