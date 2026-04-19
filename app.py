from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from models import db, Study, Sample
import pandas as pd
import plotly.express as px
import plotly.utils
import json

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///biotime.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-here'

db.init_app(app)

@app.route('/')
def index():
    """Главная страница с дашбордом"""
    total_studies = Study.query.count()
    total_samples = Sample.query.count()
    avg_species = db.session.query(db.func.avg(Study.number_of_species)).scalar() or 0
    
    # Статистика по типам биомов - преобразуем Row в кортежи
    biome_results = db.session.query(
        Study.biome_map, db.func.count(Study.id)
    ).filter(Study.biome_map != '').group_by(Study.biome_map).limit(10).all()
    # Преобразуем Row в обычные кортежи
    biome_stats = [(row[0], row[1]) for row in biome_results]
    
    # Статистика по годам - преобразуем Row в кортежи
    year_results = db.session.query(
        Study.start_year, db.func.count(Study.id)
    ).filter(Study.start_year > 0).group_by(Study.start_year).order_by(Study.start_year).all()
    # Преобразуем в список списков для JSON сериализации
    year_stats = [[row[0], row[1]] for row in year_results]
    
    return render_template('index.html',
                         total_studies=total_studies,
                         total_samples=total_samples,
                         avg_species=round(avg_species, 1),
                         biome_stats=biome_stats,
                         year_stats=year_stats)

@app.route('/studies')
def studies():
    """Список всех исследований с фильтрацией и пагинацией"""
    page = request.args.get('page', 1, type=int)
    realm = request.args.get('realm', '')
    taxa = request.args.get('taxa', '')
    
    query = Study.query
    
    if realm:
        query = query.filter(Study.realm == realm)
    if taxa:
        query = query.filter(Study.taxa == taxa)
    
    pagination = query.paginate(page=page, per_page=20, error_out=False)
    studies = pagination.items
    
    # Уникальные значения для фильтров - преобразуем Row в простые строки
    realms_results = db.session.query(Study.realm).distinct().all()
    realms = [r[0] for r in realms_results if r[0]]
    
    taxas_results = db.session.query(Study.taxa).distinct().all()
    taxas = [t[0] for t in taxas_results if t[0]]
    
    return render_template('studies.html',
                         studies=studies,
                         pagination=pagination,
                         realms=realms,
                         taxas=taxas,
                         selected_realm=realm,
                         selected_taxa=taxa)

@app.route('/study/<int:study_id>')
def study_detail(study_id):
    """Детальная страница исследования"""
    study = Study.query.get_or_404(study_id)
    samples = Sample.query.filter_by(study_id=study.id).all()
    return render_template('study_detail.html', study=study, samples=samples)

@app.route('/study/add', methods=['GET', 'POST'])
def add_study():
    """Добавление нового исследования"""
    if request.method == 'POST':
        study = Study(
            study_id=request.form.get('study_id', 0, type=int),
            realm=request.form.get('realm', ''),
            climate=request.form.get('climate', ''),
            habitat=request.form.get('habitat', ''),
            protected_area='protected_area' in request.form,
            biome_map=request.form.get('biome_map', ''),
            taxa=request.form.get('taxa', ''),
            title=request.form.get('title', ''),
            start_year=request.form.get('start_year', 0, type=int),
            end_year=request.form.get('end_year', 0, type=int),
            cent_lat=request.form.get('cent_lat', 0.0, type=float),
            cent_long=request.form.get('cent_long', 0.0, type=float),
            number_of_species=request.form.get('number_of_species', 0, type=int)
        )
        db.session.add(study)
        db.session.commit()
        flash('Исследование успешно добавлено!', 'success')
        return redirect(url_for('study_detail', study_id=study.id))
    
    return render_template('add_study.html')

@app.route('/study/<int:study_id>/edit', methods=['GET', 'POST'])
def edit_study(study_id):
    """Редактирование исследования"""
    study = Study.query.get_or_404(study_id)
    
    if request.method == 'POST':
        study.realm = request.form.get('realm', '')
        study.climate = request.form.get('climate', '')
        study.habitat = request.form.get('habitat', '')
        study.protected_area = 'protected_area' in request.form
        study.biome_map = request.form.get('biome_map', '')
        study.taxa = request.form.get('taxa', '')
        study.title = request.form.get('title', '')
        study.start_year = request.form.get('start_year', 0, type=int)
        study.end_year = request.form.get('end_year', 0, type=int)
        study.cent_lat = request.form.get('cent_lat', 0.0, type=float)
        study.cent_long = request.form.get('cent_long', 0.0, type=float)
        study.number_of_species = request.form.get('number_of_species', 0, type=int)
        
        db.session.commit()
        flash('Исследование успешно обновлено!', 'success')
        return redirect(url_for('study_detail', study_id=study.id))
    
    return render_template('edit_study.html', study=study)

@app.route('/study/<int:study_id>/delete', methods=['POST'])
def delete_study(study_id):
    """Удаление исследования"""
    study = Study.query.get_or_404(study_id)
    db.session.delete(study)
    db.session.commit()
    flash('Исследование удалено!', 'success')
    return redirect(url_for('studies'))

@app.route('/sample/<int:sample_id>/edit', methods=['POST'])
def edit_sample(sample_id):
    """Редактирование образца (AJAX)"""
    sample = Sample.query.get_or_404(sample_id)
    sample.abundance = float(request.form.get('abundance', 0))
    sample.biomass = float(request.form.get('biomass', 0))
    sample.year = int(request.form.get('year', 0))
    db.session.commit()
    return jsonify({'success': True})

@app.route('/analytics')
def analytics():
    """Страница аналитики с графиками"""
    # Данные для графиков
    df = pd.read_sql(Study.query.statement, db.session.bind)
    
    # График 1: Распределение по царствам
    realm_counts = df[df['realm'] != '']['realm'].value_counts().head(10)
    if len(realm_counts) > 0:
        fig1 = px.bar(x=realm_counts.index.tolist(), y=realm_counts.values.tolist(), 
                      title='Количество исследований по типам биомов',
                      labels={'x': 'Биом', 'y': 'Количество'})
    else:
        fig1 = px.bar(title='Нет данных')
    
    # График 2: Тренд по годам
    year_df = df[df['start_year'] > 0].groupby('start_year').size().reset_index(name='count')
    if len(year_df) > 0:
        fig2 = px.line(year_df, x='start_year', y='count',
                       title='Динамика начала исследований по годам',
                       labels={'start_year': 'Год начала', 'count': 'Количество'})
    else:
        fig2 = px.line(title='Нет данных')
    
    # График 3: Топ-10 таксонов
    taxa_counts = df[df['taxa'] != '']['taxa'].value_counts().head(10)
    if len(taxa_counts) > 0:
        fig3 = px.pie(values=taxa_counts.values.tolist(), names=taxa_counts.index.tolist(),
                      title='Распределение исследований по таксонам')
    else:
        fig3 = px.pie(title='Нет данных')
    
    # График 4: Соотношение protected/unprotected
    protected_counts = df['protected_area'].value_counts()
    if len(protected_counts) > 0:
        fig4 = px.pie(values=protected_counts.values.tolist(), 
                      names=['Protected', 'Not Protected'],
                      title='Исследования на охраняемых территориях')
    else:
        fig4 = px.pie(title='Нет данных')
    
    # Конвертация графиков в JSON для передачи в шаблон
    graphs = {
        'fig1': json.dumps(fig1, cls=plotly.utils.PlotlyJSONEncoder),
        'fig2': json.dumps(fig2, cls=plotly.utils.PlotlyJSONEncoder),
        'fig3': json.dumps(fig3, cls=plotly.utils.PlotlyJSONEncoder),
        'fig4': json.dumps(fig4, cls=plotly.utils.PlotlyJSONEncoder)
    }
    
    # Дополнительная статистика
    stats = {
        'total_studies': len(df),
        'total_species': int(df['number_of_species'].sum()) if len(df) > 0 else 0,
        'avg_duration': int(df['end_year'].mean() - df['start_year'].mean()) if len(df) > 0 and (df['start_year'] > 0).any() else 0,
        'unique_habitats': df['habitat'].nunique() if len(df) > 0 else 0
    }
    
    return render_template('analytics.html', graphs=graphs, stats=stats)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)
