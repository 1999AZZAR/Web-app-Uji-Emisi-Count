from flask import Blueprint, render_template, request, jsonify, current_app, send_file, redirect, url_for, flash
from sqlalchemy import exc, func, extract, case, distinct
from extensions import db
from models import Kendaraan, HasilUji, User
from flask_login import login_required, current_user
import tempfile
from io import BytesIO
import csv
import xlsxwriter
import time
from datetime import datetime, timedelta
import json
import os

reports = Blueprint('reports', __name__)

@reports.route('/reports')
@login_required
def dashboard():
    """Main reports dashboard"""
    try:
        # Get filter parameters
        plat_nomor = request.args.get('plat_nomor', '')
        merek = request.args.get('merek', '')
        start_date = request.args.get('start_date', '')
        end_date = request.args.get('end_date', '')
        result = request.args.get('result', '')  # 'pass', 'fail', or ''
        
        # Pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # Get required data for the dashboard
        total_kendaraan = Kendaraan.query.count()
        total_valid = HasilUji.query.filter_by(valid=True).count()
        total_lulus = HasilUji.query.filter_by(lulus=True).count()
        
        # Get combined data for vehicles and test results
        query = db.session.query(
            HasilUji, 
            Kendaraan,
            User
        ).join(
            Kendaraan, HasilUji.kendaraan_id == Kendaraan.id
        ).outerjoin(
            User, HasilUji.user_id == User.id
        )
        
        # Apply filters
        if plat_nomor:
            query = query.filter(Kendaraan.plat_nomor.ilike(f'%{plat_nomor}%'))
        if merek:
            query = query.filter(Kendaraan.merek.ilike(f'%{merek}%'))
        if start_date:
            try:
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
                query = query.filter(HasilUji.tanggal >= start_date_obj)
            except ValueError:
                pass
        if end_date:
            try:
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
                # Set end_date to end of day
                end_date_obj = datetime(end_date_obj.year, end_date_obj.month, end_date_obj.day, 23, 59, 59)
                query = query.filter(HasilUji.tanggal <= end_date_obj)
            except ValueError:
                pass
        if result == 'pass':
            query = query.filter(HasilUji.lulus == True)
        elif result == 'fail':
            query = query.filter(HasilUji.lulus == False)
            
        # Order by date (newest first)
        query = query.order_by(HasilUji.tanggal.desc())
        
        # Count total results for pagination
        total_results = query.count()
        
        # Apply pagination
        results = query.limit(per_page).offset((page - 1) * per_page).all()
        
        # Format the data for template
        formatted_data = []
        for hasil, kendaraan, user in results:
            formatted_data.append({
                'hasil': hasil,
                'kendaraan': kendaraan,
                'operator': user.username if user else 'Unknown'
            })
        
        # If filters are applied, update counts based on filtered query
        if plat_nomor or merek or start_date or end_date or result:
            valid_count = query.filter(HasilUji.valid == True).count()
            pass_count = query.filter(HasilUji.lulus == True).count()
            
            # Override stats with filtered data
            total_valid = valid_count
            total_lulus = pass_count
        
        # Calculate pagination metadata
        total_pages = (total_results + per_page - 1) // per_page
        has_prev = page > 1
        has_next = page < total_pages
        
        return render_template(
            'halaman3.html',
            total_kendaraan=total_kendaraan,
            total_valid=total_valid,
            total_lulus=total_lulus,
            data=formatted_data,
            # Pagination data
            page=page,
            per_page=per_page,
            total_pages=total_pages,
            total_results=total_results,
            has_prev=has_prev,
            has_next=has_next
        )
    except Exception as e:
        current_app.logger.error(f"Error in dashboard: {str(e)}")
        flash(f"Error loading dashboard: {str(e)}", "error")
        return render_template(
            'halaman3.html', 
            total_kendaraan=0,
            total_valid=0,
            total_lulus=0,
            data=[],
            # Add pagination data to avoid template errors
            page=1,
            per_page=20,
            total_pages=0,
            total_results=0,
            has_prev=False,
            has_next=False
        )

@reports.route('/api/statistics')
@login_required
def statistics():
    """Get global statistics for dashboard"""
    try:
        total_kendaraan = Kendaraan.query.count()
        total_tests = HasilUji.query.filter_by(valid=True).count()
        passing_tests = HasilUji.query.filter_by(lulus=True).count()
        failing_tests = HasilUji.query.filter_by(lulus=False, valid=True).count()
        
        # Calculate pass rate
        pass_rate = 0
        if total_tests > 0:
            pass_rate = (passing_tests / total_tests) * 100
            
        # Get vehicle type distribution
        vehicle_types = db.session.query(
            Kendaraan.fuel_type,
            func.count(Kendaraan.id)
        ).group_by(Kendaraan.fuel_type).all()
        
        vehicle_type_data = {
            'bensin': 0,
            'solar': 0
        }
        for fuel_type, count in vehicle_types:
            vehicle_type_data[fuel_type] = count
            
        # Get test results by month (last 6 months)
        today = datetime.today()
        six_months_ago = today - timedelta(days=180)
        
        monthly_results = db.session.query(
            extract('year', HasilUji.tanggal).label('year'),
            extract('month', HasilUji.tanggal).label('month'),
            func.count(case([(HasilUji.lulus == True, 1)])).label('passing'),
            func.count(case([(HasilUji.lulus == False, 1)])).label('failing')
        ).filter(
            HasilUji.tanggal >= six_months_ago,
            HasilUji.valid == True
        ).group_by(
            extract('year', HasilUji.tanggal),
            extract('month', HasilUji.tanggal)
        ).order_by(
            extract('year', HasilUji.tanggal),
            extract('month', HasilUji.tanggal)
        ).all()
        
        monthly_data = []
        for year, month, passing, failing in monthly_results:
            month_name = datetime(int(year), int(month), 1).strftime('%b %Y')
            monthly_data.append({
                'month': month_name,
                'passing': passing,
                'failing': failing,
                'total': passing + failing
            })
            
        # Recent test results (last 10)
        recent_tests = db.session.query(HasilUji, Kendaraan).join(
            Kendaraan, HasilUji.kendaraan_id == Kendaraan.id
        ).order_by(
            HasilUji.tanggal.desc()
        ).limit(10).all()
        
        recent_data = []
        for hasil, kendaraan in recent_tests:
            recent_data.append({
                'id': hasil.id,
                'plat_nomor': kendaraan.plat_nomor,
                'merek': kendaraan.merek,
                'tipe': kendaraan.tipe,
                'tanggal': hasil.tanggal.strftime('%Y-%m-%d %H:%M'),
                'lulus': hasil.lulus,
                'fuel_type': kendaraan.fuel_type
            })
            
        return jsonify({
            'total_kendaraan': total_kendaraan,
            'total_tests': total_tests,
            'passing_tests': passing_tests,
            'failing_tests': failing_tests,
            'pass_rate': round(pass_rate, 1),
            'vehicle_types': vehicle_type_data,
            'monthly_results': monthly_data,
            'recent_tests': recent_data
        })
    except Exception as e:
        current_app.logger.error(str(e))
        return jsonify({'error': str(e)}), 500

@reports.route('/api/reports/emissions-by-type')
@login_required
def emissions_by_type():
    """Get average emissions by vehicle type"""
    try:
        # For bensin vehicles
        bensin_results = db.session.query(
            Kendaraan.load_category,
            func.avg(HasilUji.co).label('avg_co'),
            func.avg(HasilUji.co2).label('avg_co2'),
            func.avg(HasilUji.hc).label('avg_hc'),
            func.avg(HasilUji.o2).label('avg_o2'),
            func.avg(HasilUji.lambda_val).label('avg_lambda')
        ).join(
            HasilUji, Kendaraan.id == HasilUji.kendaraan_id
        ).filter(
            Kendaraan.fuel_type == 'bensin',
            HasilUji.valid == True
        ).group_by(
            Kendaraan.load_category
        ).all()
        
        bensin_data = []
        for category, avg_co, avg_co2, avg_hc, avg_o2, avg_lambda in bensin_results:
            display_name = 'Kendaraan Muatan' if category == 'kendaraan_muatan' else 'Kendaraan Penumpang'
            bensin_data.append({
                'category': display_name,
                'avg_co': round(avg_co, 2) if avg_co else 0,
                'avg_co2': round(avg_co2, 2) if avg_co2 else 0,
                'avg_hc': round(avg_hc, 2) if avg_hc else 0,
                'avg_o2': round(avg_o2, 2) if avg_o2 else 0,
                'avg_lambda': round(avg_lambda, 2) if avg_lambda else 0
            })
            
        # For solar vehicles
        solar_results = db.session.query(
            Kendaraan.load_category,
            func.avg(HasilUji.opacity).label('avg_opacity')
        ).join(
            HasilUji, Kendaraan.id == HasilUji.kendaraan_id
        ).filter(
            Kendaraan.fuel_type == 'solar',
            HasilUji.valid == True
        ).group_by(
            Kendaraan.load_category
        ).all()
        
        solar_data = []
        for category, avg_opacity in solar_results:
            display_name = 'Kurang dari 3.5 Ton' if category == '<3.5ton' else 'Lebih dari atau sama dengan 3.5 Ton'
            solar_data.append({
                'category': display_name,
                'avg_opacity': round(avg_opacity, 2) if avg_opacity else 0
            })
            
        return jsonify({
            'bensin': bensin_data,
            'solar': solar_data
        })
    except Exception as e:
        current_app.logger.error(str(e))
        return jsonify({'error': str(e)}), 500

@reports.route('/api/reports/vehicle-age-performance')
@login_required
def vehicle_age_performance():
    """Get pass/fail statistics by vehicle age"""
    try:
        current_year = datetime.now().year
        
        # Age categories: 0-5, 6-10, 11-15, 16+
        age_categories = [
            {'min': 0, 'max': 5, 'label': '0-5 tahun'},
            {'min': 6, 'max': 10, 'label': '6-10 tahun'},
            {'min': 11, 'max': 15, 'label': '11-15 tahun'},
            {'min': 16, 'max': 100, 'label': '16+ tahun'}
        ]
        
        results = []
        
        for category in age_categories:
            min_year = current_year - category['max']
            max_year = current_year - category['min']
            
            # Get passing and failing counts
            data = db.session.query(
                func.count(case([(HasilUji.lulus == True, 1)])).label('passing'),
                func.count(case([(HasilUji.lulus == False, 1)])).label('failing')
            ).join(
                Kendaraan, HasilUji.kendaraan_id == Kendaraan.id
            ).filter(
                Kendaraan.tahun >= min_year,
                Kendaraan.tahun <= max_year,
                HasilUji.valid == True
            ).first()
            
            passing = data.passing if data else 0
            failing = data.failing if data else 0
            total = passing + failing
            
            pass_rate = 0
            if total > 0:
                pass_rate = (passing / total) * 100
                
            results.append({
                'age_range': category['label'],
                'passing': passing,
                'failing': failing,
                'total': total,
                'pass_rate': round(pass_rate, 1)
            })
            
        return jsonify(results)
    except Exception as e:
        current_app.logger.error(str(e))
        return jsonify({'error': str(e)}), 500

@reports.route('/export-excel')
@login_required
def export_excel():
    """Export detailed test results to Excel"""
    try:
        # Filter parameters
        plat_nomor = request.args.get('plat_nomor', '')
        merek = request.args.get('merek', '')
        start_date = request.args.get('start_date', '')
        end_date = request.args.get('end_date', '')
        result = request.args.get('result', '')  # 'pass', 'fail', or ''
        
        # Base query joining all tables
        query = db.session.query(HasilUji, Kendaraan, User).join(
            Kendaraan, HasilUji.kendaraan_id == Kendaraan.id
        ).outerjoin(
            User, HasilUji.user_id == User.id
        )
        
        # Apply filters
        if plat_nomor:
            query = query.filter(Kendaraan.plat_nomor.ilike(f'%{plat_nomor}%'))
        if merek:
            query = query.filter(Kendaraan.merek.ilike(f'%{merek}%'))
        if start_date:
            try:
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
                query = query.filter(HasilUji.tanggal >= start_date_obj)
            except ValueError:
                pass
        if end_date:
            try:
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
                end_date_obj = datetime(end_date_obj.year, end_date_obj.month, end_date_obj.day, 23, 59, 59)
                query = query.filter(HasilUji.tanggal <= end_date_obj)
            except ValueError:
                pass
        if result == 'pass':
            query = query.filter(HasilUji.lulus == True)
        elif result == 'fail':
            query = query.filter(HasilUji.lulus == False)
            
        # Order by date
        query = query.order_by(HasilUji.tanggal.desc())
        
        # Get results
        results = query.all()
        
        # Create Excel file in memory
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('Test Results')
        
        # Add header row with formatting
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#4472C4',
            'font_color': 'white',
            'border': 1
        })
        
        # Define data formats
        date_format = workbook.add_format({'num_format': 'yyyy-mm-dd hh:mm:ss'})
        
        pass_format = workbook.add_format({
            'bg_color': '#C6EFCE',
            'font_color': '#006100'
        })
        
        fail_format = workbook.add_format({
            'bg_color': '#FFC7CE',
            'font_color': '#9C0006'
        })
        
        # Set up header row
        headers = [
            'Tanggal Uji', 'Plat Nomor', 'Merek', 'Tipe', 'Tahun',
            'Bahan Bakar', 'Kategori Beban', 'CO (%)', 'CO2 (%)',
            'HC (ppm)', 'O2 (%)', 'Lambda', 'Opacity (%)', 'Hasil',
            'Operator'
        ]
        
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)
            
        # Set column widths
        worksheet.set_column('A:A', 20)  # Date
        worksheet.set_column('B:B', 15)  # Plate
        worksheet.set_column('C:D', 15)  # Make/Model
        worksheet.set_column('E:G', 15)  # Year/Fuel/Category
        worksheet.set_column('H:M', 12)  # Test values
        worksheet.set_column('N:N', 10)  # Result
        worksheet.set_column('O:O', 15)  # Operator
        
        # Write data rows
        for i, (hasil, kendaraan, user) in enumerate(results, start=1):
            row = [
                hasil.tanggal,
                kendaraan.plat_nomor,
                kendaraan.merek,
                kendaraan.tipe,
                kendaraan.tahun,
                'Bensin' if kendaraan.fuel_type == 'bensin' else 'Solar',
                display_load_category(kendaraan.load_category),
                hasil.co,
                hasil.co2,
                hasil.hc,
                hasil.o2,
                hasil.lambda_val,
                hasil.opacity,
                'LULUS' if hasil.lulus else 'GAGAL',
                user.username if user else 'Unknown'
            ]
            
            # Apply formatting
            result_format = pass_format if hasil.lulus else fail_format
            
            # Write each cell with appropriate formatting
            for col, value in enumerate(row):
                if col == 0:  # Date column
                    worksheet.write_datetime(i, col, value, date_format)
                elif col == 13:  # Result column
                    worksheet.write(i, col, value, result_format)
                else:
                    worksheet.write(i, col, value)
                    
        # Add auto-filter
        worksheet.autofilter(0, 0, len(results), len(headers) - 1)
        
        # Add second worksheet for summary
        summary_sheet = workbook.add_worksheet('Summary')
        
        # Add title with formatting
        title_format = workbook.add_format({
            'bold': True,
            'font_size': 14,
            'align': 'center',
            'valign': 'vcenter'
        })
        
        section_format = workbook.add_format({
            'bold': True,
            'font_size': 12,
            'bg_color': '#D9E1F2',
            'border': 1
        })
        
        # Calculate summary statistics
        total_tests = len(results)
        passing_tests = sum(1 for hasil, _, _ in results if hasil.lulus)
        failing_tests = total_tests - passing_tests
        pass_rate = (passing_tests / total_tests * 100) if total_tests > 0 else 0
        
        # Add title
        summary_sheet.merge_range('A1:D1', 'Laporan Ringkasan Uji Emisi', title_format)
        summary_sheet.set_column('A:A', 25)
        summary_sheet.set_column('B:D', 15)
        
        # Basic statistics
        summary_sheet.write(2, 0, 'Statistik Dasar', section_format)
        summary_sheet.merge_range('B3:D3', '', section_format)
        
        row = 3
        summary_sheet.write(row, 0, 'Total Pengujian')
        summary_sheet.write(row, 1, total_tests)
        
        row += 1
        summary_sheet.write(row, 0, 'Pengujian Lulus')
        summary_sheet.write(row, 1, passing_tests)
        
        row += 1
        summary_sheet.write(row, 0, 'Pengujian Gagal')
        summary_sheet.write(row, 1, failing_tests)
        
        row += 1
        summary_sheet.write(row, 0, 'Tingkat Kelulusan')
        summary_sheet.write(row, 1, f'{pass_rate:.1f}%')
        
        # By fuel type
        row += 2
        summary_sheet.write(row, 0, 'Berdasarkan Bahan Bakar', section_format)
        summary_sheet.merge_range(f'B{row+1}:D{row+1}', '', section_format)
        
        # Bensin statistics
        bensin_tests = [(hasil, kendaraan) for hasil, kendaraan, _ in results if kendaraan.fuel_type == 'bensin']
        bensin_total = len(bensin_tests)
        bensin_passing = sum(1 for hasil, _ in bensin_tests if hasil.lulus)
        bensin_rate = (bensin_passing / bensin_total * 100) if bensin_total > 0 else 0
        
        row += 1
        summary_sheet.write(row, 0, 'Total Bensin')
        summary_sheet.write(row, 1, bensin_total)
        
        row += 1
        summary_sheet.write(row, 0, 'Lulus (Bensin)')
        summary_sheet.write(row, 1, bensin_passing)
        
        row += 1
        summary_sheet.write(row, 0, 'Tingkat Kelulusan (Bensin)')
        summary_sheet.write(row, 1, f'{bensin_rate:.1f}%')
        
        # Solar statistics
        solar_tests = [(hasil, kendaraan) for hasil, kendaraan, _ in results if kendaraan.fuel_type == 'solar']
        solar_total = len(solar_tests)
        solar_passing = sum(1 for hasil, _ in solar_tests if hasil.lulus)
        solar_rate = (solar_passing / solar_total * 100) if solar_total > 0 else 0
        
        row += 1
        summary_sheet.write(row, 0, 'Total Solar')
        summary_sheet.write(row, 1, solar_total)
        
        row += 1
        summary_sheet.write(row, 0, 'Lulus (Solar)')
        summary_sheet.write(row, 1, solar_passing)
        
        row += 1
        summary_sheet.write(row, 0, 'Tingkat Kelulusan (Solar)')
        summary_sheet.write(row, 1, f'{solar_rate:.1f}%')
        
        # Report metadata
        row += 2
        summary_sheet.write(row, 0, 'Informasi Laporan', section_format)
        summary_sheet.merge_range(f'B{row+1}:D{row+1}', '', section_format)
        
        row += 1
        summary_sheet.write(row, 0, 'Laporan Dibuat Oleh')
        summary_sheet.write(row, 1, current_user.username)
        
        row += 1
        summary_sheet.write(row, 0, 'Tanggal Laporan')
        summary_sheet.write_datetime(row, 1, datetime.now(), date_format)
        
        # Filter details
        if any([plat_nomor, merek, start_date, end_date, result]):
            row += 2
            summary_sheet.write(row, 0, 'Filter yang Digunakan', section_format)
            summary_sheet.merge_range(f'B{row+1}:D{row+1}', '', section_format)
            
            if plat_nomor:
                row += 1
                summary_sheet.write(row, 0, 'Plat Nomor')
                summary_sheet.write(row, 1, plat_nomor)
                
            if merek:
                row += 1
                summary_sheet.write(row, 0, 'Merek')
                summary_sheet.write(row, 1, merek)
                
            if start_date:
                row += 1
                summary_sheet.write(row, 0, 'Dari Tanggal')
                summary_sheet.write(row, 1, start_date)
                
            if end_date:
                row += 1
                summary_sheet.write(row, 0, 'Sampai Tanggal')
                summary_sheet.write(row, 1, end_date)
                
            if result:
                row += 1
                summary_sheet.write(row, 0, 'Hasil Uji')
                summary_sheet.write(row, 1, 'LULUS' if result == 'pass' else 'GAGAL')
        
        # Close workbook
        workbook.close()
        
        # Reset file pointer
        output.seek(0)
        
        # Generate filename with timestamp
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        filename = f'laporan_uji_emisi_{timestamp}.xlsx'
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
            tmp.write(output.read())
            tmp_path = tmp.name
            
        return send_file(
            tmp_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        current_app.logger.error(str(e))
        flash('Error generating Excel report', 'error')
        return redirect(url_for('reports.dashboard'))

# Helper function to display load category in a human-readable format
def display_load_category(category):
    if category == 'kendaraan_muatan':
        return 'Kendaraan Muatan'
    elif category == 'kendaraan_penumpang':
        return 'Kendaraan Penumpang'
    elif category == '<3.5ton':
        return 'Kurang dari 3.5 Ton'
    elif category == '>=3.5ton':
        return 'Lebih dari atau sama dengan 3.5 Ton'
    else:
        return category 