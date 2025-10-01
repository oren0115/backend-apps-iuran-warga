from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import Response
from fastapi.responses import StreamingResponse
from app.models.schemas import (
    UserResponse, FeeResponse, PaymentResponse, MessageResponse, 
    GenerateFeesRequest, NotificationResponse, UserUpdate, PasswordUpdate, UserCreate, ResetPasswordRequest
)
from app.controllers.user_controller import UserController
from app.controllers.fee_controller import FeeController
from app.controllers.payment_controller import PaymentController
from app.controllers.notification_controller import NotificationController
from app.controllers.admin_controller import AdminController
from app.utils.auth import get_current_admin
from app.config.database import get_database
from fastapi import Path
from typing import List
from datetime import datetime, date
import io
import pandas as pd

router = APIRouter()
user_controller = UserController()
fee_controller = FeeController()
payment_controller = PaymentController()
notification_controller = NotificationController()
admin_controller = AdminController()

# User Management
@router.post("/users", response_model=UserResponse)
async def create_user(user_data: UserCreate, current_user = Depends(get_current_admin)):
    """Create a new user (admin only)"""
    return await user_controller.register_user(user_data)

@router.get("/users", response_model=List[UserResponse])
async def get_all_users(current_user = Depends(get_current_admin)):
    """Get all users (admin only)"""
    return await user_controller.get_all_users()

@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user_profile_admin(
    user_id: str = Path(..., description="ID pengguna"),
    updates: UserUpdate = None,
    current_user = Depends(get_current_admin)
):
    """Update user profile by id (admin only)"""
    return await user_controller.update_user_by_id(user_id, updates)

@router.put("/users/{user_id}/password", response_model=MessageResponse)
async def update_user_password_admin(
    user_id: str = Path(..., description="ID pengguna"),
    payload: PasswordUpdate = None,
    current_user = Depends(get_current_admin)
):
    """Update user password by id (admin only)"""
    return await user_controller.update_user_password_by_id(user_id, payload)

@router.delete("/users/{user_id}", response_model=MessageResponse)
async def delete_user_admin(
    user_id: str = Path(..., description="ID pengguna"),
    current_user = Depends(get_current_admin)
):
    """Delete user by id (admin only)"""
    return await user_controller.delete_user_by_id(user_id)

@router.patch("/users/{user_id}/promote", response_model=UserResponse)
async def promote_user_to_admin(
    user_id: str = Path(..., description="ID pengguna"),
    current_user = Depends(get_current_admin)
):
    """Promote user to admin (admin only)"""
    return await user_controller.promote_user_to_admin(user_id)

@router.patch("/users/{user_id}/demote", response_model=UserResponse)
async def demote_user_from_admin(
    user_id: str = Path(..., description="ID pengguna"),
    current_user = Depends(get_current_admin)
):
    """Demote user from admin (admin only)"""
    return await user_controller.demote_user_from_admin(user_id)

@router.patch("/users/{user_id}/reset-password", response_model=MessageResponse)
async def reset_user_password_admin(
    user_id: str = Path(..., description="ID pengguna"),
    request: ResetPasswordRequest = None,
    current_user = Depends(get_current_admin)
):
    """Reset user password by id (admin only)"""
    return await user_controller.reset_user_password_by_id(user_id, request.password)

# Fee Management
@router.post("/generate-fees", response_model=MessageResponse)
async def generate_monthly_fees(request: GenerateFeesRequest, current_user = Depends(get_current_admin)):
    """Generate monthly fees for all users (admin only)
    Tarif IPL dikirim dari frontend berdasarkan tipe rumah.
    """
    tarif_config = {
        "60M2": request.tarif_60m2,
        "72M2": request.tarif_72m2,
        "HOOK": request.tarif_hook,
    }
    return await fee_controller.generate_monthly_fees(request.bulan, tarif_config)

@router.get("/fees", response_model=List[FeeResponse])
async def get_all_fees(current_user = Depends(get_current_admin)):
    """Get all fees (admin only)"""
    return await fee_controller.get_all_fees()

@router.post("/regenerate-fees", response_model=MessageResponse)
async def regenerate_fees_for_month(request: GenerateFeesRequest, current_user = Depends(get_current_admin)):
    """Regenerate fees for a specific month based on current user house types (admin only)"""
    tarif_config = {
        "60M2": request.tarif_60m2,
        "72M2": request.tarif_72m2,
        "HOOK": request.tarif_hook,
    }
    return await fee_controller.regenerate_fees_for_month(request.bulan, tarif_config)

# Payment Management
@router.get("/payments", response_model=List[PaymentResponse])
async def get_all_payments(current_user = Depends(get_current_admin)):
    """Get all payments (admin only)"""
    return await payment_controller.get_all_payments()

# Notification Management
@router.post("/notifications/broadcast", response_model=MessageResponse)
async def broadcast_notification(
    title: str,
    message: str,
    notification_type: str = "pengumuman",
    current_user = Depends(get_current_admin)
):
    """Send notification to all users (admin only)"""
    return await notification_controller.create_bulk_notifications(title, message, notification_type)

# Dashboard
@router.get("/dashboard")
async def get_dashboard_stats(current_user = Depends(get_current_admin)):
    """Get dashboard statistics (admin only)"""
    return await admin_controller.get_dashboard_stats()

# Sample Data
@router.post("/init-sample-data", response_model=MessageResponse)
async def init_sample_data():
    """Initialize sample data for testing"""
    return await admin_controller.init_sample_data()

# Reports Export
@router.get("/reports/fees/export")
async def export_fees(
    bulan: str = Query(..., description="Format YYYY-MM"),
    format: str = Query("excel", pattern="^(excel|pdf)$"),
    current_user = Depends(get_current_admin),
):
    data = await fee_controller.get_fees_by_month(bulan)
    # Convert Pydantic models to dicts
    records = [d.model_dump() if hasattr(d, "model_dump") else dict(d) for d in data]
    df = pd.DataFrame(records)
    if format == "excel":
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="Fees")
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="fees_{bulan}.xlsx"'},
        )
    else:
        try:
            from reportlab.pdfgen import canvas
        except ImportError:
            raise RuntimeError("PDF export requires reportlab. Please install it.")
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer)
        textobject = c.beginText(40, 800)
        textobject.textLine(f"Laporan Iuran {bulan}")
        for row in df.to_dict(orient="records"):
            textobject.textLine(str(row))
        c.drawText(textobject)
        c.showPage()
        c.save()
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="fees_{bulan}.pdf"'},
        )

@router.get("/reports/payments/export")
async def export_payments(
    start: date = Query(..., description="Start date YYYY-MM-DD"),
    end: date = Query(..., description="End date YYYY-MM-DD"),
    format: str = Query("excel", pattern="^(excel|pdf)$"),
    current_user = Depends(get_current_admin),
):
    try:
        print(f"Export request: start={start}, end={end}, format={format}")
        start_dt = datetime.combine(start, datetime.min.time())
        end_dt = datetime.combine(end, datetime.max.time())
        print(f"Date range: {start_dt} to {end_dt}")
        
        data = await payment_controller.get_payments_by_date_range(start_dt, end_dt)
        print(f"Found {len(data)} payments")
        
        # Get user data for each payment
        db = get_database()
        export_data = []
        
        for payment in data:
            try:
                # Get user information
                user = await db.users.find_one({"id": payment.user_id}, {"_id": 0})
                username = user.get("username", "Unknown") if user else "Unknown"
                
                # Format created_at to readable string
                if hasattr(payment.created_at, 'strftime'):
                    created_at_str = payment.created_at.strftime("%Y-%m-%d %H:%M:%S")
                elif isinstance(payment.created_at, str):
                    created_at_str = payment.created_at
                else:
                    created_at_str = str(payment.created_at)
                
                # Create export record with only required fields
                export_record = {
                    "ID": payment.id or "",
                    "Username": username,
                    "Jumlah Pembayaran": payment.amount or 0,
                    "Metode Pembayaran": payment.payment_method or "",
                    "Status": payment.status or "",
                    "Tanggal Pembayaran": created_at_str,
                    "ID Pembayaran": payment.transaction_id or "",
                    "URL Pembayaran": payment.payment_url or ""
                }
                export_data.append(export_record)
            except Exception as e:
                print(f"Error processing payment {payment.id}: {str(e)}")
                # Add a basic record even if there's an error
                export_record = {
                    "ID": payment.id or "",
                    "Username": "Error",
                    "Jumlah Pembayaran": 0,
                    "Metode Pembayaran": "",
                    "Status": "Error",
                    "Tanggal Pembayaran": "",
                    "ID Pembayaran": "",
                    "URL Pembayaran": ""
                }
                export_data.append(export_record)
        
        df = pd.DataFrame(export_data)
    except Exception as e:
        print(f"Error in export_payments: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")
    
    if format == "excel":
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            # First, write the DataFrame to create the worksheet
            df.to_excel(writer, index=False, sheet_name="Payments", startrow=7)
            
            # Now get the workbook and worksheet
            workbook = writer.book
            worksheet = writer.sheets["Payments"]
            
            # Define formats
            header_format = workbook.add_format({
                'bold': True,
                'font_size': 16,
                'align': 'center',
                'valign': 'vcenter',
                'bg_color': '#4CAF50',
                'font_color': 'white'
            })
            
            subheader_format = workbook.add_format({
                'bold': True,
                'font_size': 12,
                'align': 'left',
                'valign': 'vcenter'
            })
            
            info_format = workbook.add_format({
                'font_size': 10,
                'align': 'left',
                'valign': 'vcenter'
            })
            
            # Add header information
            worksheet.merge_range('A1:H1', 'LAPORAN PEMBAYARAN IPL CANNART', header_format)
            worksheet.merge_range('A2:H2', '', info_format)  # Empty row
            
            # Add export information
            current_time = datetime.now().strftime("%d %B %Y %H:%M:%S")
            worksheet.merge_range('A3:H3', f'Periode: {start} s.d {end}', subheader_format)
            worksheet.merge_range('A4:H4', f'Dibuat pada: {current_time}', info_format)
            worksheet.merge_range('A5:H5', f'Dibuat oleh: {current_user.get("username", "Unknown")}', info_format)
            worksheet.merge_range('A6:H6', f'Total Data: {len(export_data)} transaksi', info_format)
            worksheet.merge_range('A7:H7', '', info_format)  # Empty row
            
            # Adjust column widths
            worksheet.set_column('A:A', 15)  # ID
            worksheet.set_column('B:B', 15)  # Username
            worksheet.set_column('C:C', 18)  # Jumlah Pembayaran
            worksheet.set_column('D:D', 18)  # Metode Pembayaran
            worksheet.set_column('E:E', 12)  # Status
            worksheet.set_column('F:F', 20)  # Tanggal Pembayaran
            worksheet.set_column('G:G', 25)  # ID Pembayaran
            worksheet.set_column('H:H', 50)  # URL Pembayaran
            
            # Add border to data area
            data_format = workbook.add_format({
                'border': 1,
                'align': 'left',
                'valign': 'vcenter'
            })
            
            # Apply border to data rows
            for row in range(8, 8 + len(export_data) + 1):
                for col in range(8):
                    worksheet.write(row, col, '', data_format)
            
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f'attachment; filename="Laporan_Pembayaran_IPL_Cannart_{start}_{end}.xlsx"',
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization",
            },
        )
    else:
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib import colors
            from reportlab.lib.units import inch
        except ImportError:
            raise RuntimeError("PDF export requires reportlab. Please install it.")
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Add title
        title = Paragraph("LAPORAN PEMBAYARAN IPL CANNART", styles['Title'])
        story.append(title)
        story.append(Spacer(1, 12))
        
        # Add export information
        current_time = datetime.now().strftime("%d %B %Y %H:%M:%S")
        info_data = [
            [f"Periode: {start} s.d {end}"],
            [f"Dibuat pada: {current_time}"],
            [f"Dibuat oleh: {current_user.get('username', 'Unknown')}"],
            [f"Total Data: {len(export_data)} transaksi"]
        ]
        
        info_table = Table(info_data)
        info_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 20))
        
        # Add data table
        if len(export_data) > 0:
            # Prepare table data
            table_data = [list(df.columns)]  # Headers
            for _, row in df.iterrows():
                table_data.append([str(val) for val in row.values])
            
            # Create table
            data_table = Table(table_data)
            data_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(data_table)
        else:
            no_data = Paragraph("Tidak ada data pembayaran untuk periode yang dipilih.", styles['Normal'])
            story.append(no_data)
        
        doc.build(story)
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="Laporan_Pembayaran_IPL_Cannart_{start}_{end}.pdf"',
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization",
            },
        )

# Handle CORS preflight request
@router.options("/reports/payments/export")
async def export_payments_options():
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
            "Access-Control-Max-Age": "86400",
        }
    )

# Test endpoint without authentication for debugging
@router.get("/reports/payments/export-test", include_in_schema=False)
async def export_payments_test(
    start: date = Query(..., description="Start date YYYY-MM-DD"),
    end: date = Query(..., description="End date YYYY-MM-DD"),
    format: str = Query("excel", pattern="^(excel|pdf)$"),
):
    try:
        print(f"Export request: start={start}, end={end}, format={format}")
        start_dt = datetime.combine(start, datetime.min.time())
        end_dt = datetime.combine(end, datetime.max.time())
        print(f"Date range: {start_dt} to {end_dt}")
        
        data = await payment_controller.get_payments_by_date_range(start_dt, end_dt)
        print(f"Found {len(data)} payments")
        
        # Get user data for each payment
        db = get_database()
        export_data = []
        
        for payment in data:
            try:
                # Get user information
                user = await db.users.find_one({"id": payment.user_id}, {"_id": 0})
                username = user.get("username", "Unknown") if user else "Unknown"
                
                # Format created_at to readable string
                if hasattr(payment.created_at, 'strftime'):
                    created_at_str = payment.created_at.strftime("%Y-%m-%d %H:%M:%S")
                elif isinstance(payment.created_at, str):
                    created_at_str = payment.created_at
                else:
                    created_at_str = str(payment.created_at)
                
                # Create export record with only required fields
                export_record = {
                    "ID": payment.id or "",
                    "Username": username,
                    "Jumlah Pembayaran": payment.amount or 0,
                    "Metode Pembayaran": payment.payment_method or "",
                    "Status": payment.status or "",
                    "Tanggal Pembayaran": created_at_str,
                    "ID Pembayaran": payment.transaction_id or "",
                    "URL Pembayaran": payment.payment_url or ""
                }
                export_data.append(export_record)
            except Exception as e:
                print(f"Error processing payment {payment.id}: {str(e)}")
                # Add a basic record even if there's an error
                export_record = {
                    "ID": payment.id or "",
                    "Username": "Error",
                    "Jumlah Pembayaran": 0,
                    "Metode Pembayaran": "",
                    "Status": "Error",
                    "Tanggal Pembayaran": "",
                    "ID Pembayaran": "",
                    "URL Pembayaran": ""
                }
                export_data.append(export_record)
        
        df = pd.DataFrame(export_data)
        
        if format == "excel":
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
                # First, write the DataFrame to create the worksheet
                df.to_excel(writer, index=False, sheet_name="Payments", startrow=7)
                
                # Now get the workbook and worksheet
                workbook = writer.book
                worksheet = writer.sheets["Payments"]
                
                # Define formats
                header_format = workbook.add_format({
                    'bold': True,
                    'font_size': 16,
                    'align': 'center',
                    'valign': 'vcenter',
                    'bg_color': '#4CAF50',
                    'font_color': 'white'
                })
                
                subheader_format = workbook.add_format({
                    'bold': True,
                    'font_size': 12,
                    'align': 'left',
                    'valign': 'vcenter'
                })
                
                info_format = workbook.add_format({
                    'font_size': 10,
                    'align': 'left',
                    'valign': 'vcenter'
                })
                
                # Add header information
                worksheet.merge_range('A1:H1', 'LAPORAN PEMBAYARAN IPL CANNART', header_format)
                worksheet.merge_range('A2:H2', '', info_format)  # Empty row
                
                # Add export information
                current_time = datetime.now().strftime("%d %B %Y %H:%M:%S")
                worksheet.merge_range('A3:H3', f'Periode: {start} s.d {end}', subheader_format)
                worksheet.merge_range('A4:H4', f'Dibuat pada: {current_time}', info_format)
                worksheet.merge_range('A5:H5', f'Dibuat oleh: Test User', info_format)
                worksheet.merge_range('A6:H6', f'Total Data: {len(export_data)} transaksi', info_format)
                worksheet.merge_range('A7:H7', '', info_format)  # Empty row
                
                # Adjust column widths
                worksheet.set_column('A:A', 15)  # ID
                worksheet.set_column('B:B', 15)  # Username
                worksheet.set_column('C:C', 18)  # Jumlah Pembayaran
                worksheet.set_column('D:D', 18)  # Metode Pembayaran
                worksheet.set_column('E:E', 12)  # Status
                worksheet.set_column('F:F', 20)  # Tanggal Pembayaran
                worksheet.set_column('G:G', 25)  # ID Pembayaran
                worksheet.set_column('H:H', 50)  # URL Pembayaran
                
            buffer.seek(0)
            return StreamingResponse(
                buffer,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f'attachment; filename="Laporan_Pembayaran_IPL_Cannart_{start}_{end}.xlsx"'},
            )
        else:
            return {"message": "PDF export not implemented for test endpoint", "data": export_data}
            
    except Exception as e:
        print(f"Error in export_payments_test: {str(e)}")
        return {"error": str(e), "message": "Export test failed"}

# Simple test endpoint
@router.get("/test-export")
async def test_export():
    return {"message": "Export test endpoint is working", "status": "OK"}

# Export endpoint without authentication for testing
@router.get("/reports/payments/export-no-auth")
async def export_payments_no_auth(
    start: date = Query(..., description="Start date YYYY-MM-DD"),
    end: date = Query(..., description="End date YYYY-MM-DD"),
    format: str = Query("excel", pattern="^(excel|pdf)$"),
):
    try:
        print(f"Export request (no auth): start={start}, end={end}, format={format}")
        start_dt = datetime.combine(start, datetime.min.time())
        end_dt = datetime.combine(end, datetime.max.time())
        print(f"Date range: {start_dt} to {end_dt}")
        
        data = await payment_controller.get_payments_by_date_range(start_dt, end_dt)
        print(f"Found {len(data)} payments")
        
        # Get user data for each payment
        db = get_database()
        export_data = []
        
        for payment in data:
            try:
                # Get user information
                user = await db.users.find_one({"id": payment.user_id}, {"_id": 0})
                username = user.get("username", "Unknown") if user else "Unknown"
                
                # Format created_at to readable string
                if hasattr(payment.created_at, 'strftime'):
                    created_at_str = payment.created_at.strftime("%Y-%m-%d %H:%M:%S")
                elif isinstance(payment.created_at, str):
                    created_at_str = payment.created_at
                else:
                    created_at_str = str(payment.created_at)
                
                # Create export record with only required fields
                export_record = {
                    "ID": payment.id or "",
                    "Username": username,
                    "Jumlah Pembayaran": payment.amount or 0,
                    "Metode Pembayaran": payment.payment_method or "",
                    "Status": payment.status or "",
                    "Tanggal Pembayaran": created_at_str,
                    "ID Pembayaran": payment.transaction_id or "",
                    "URL Pembayaran": payment.payment_url or ""
                }
                export_data.append(export_record)
            except Exception as e:
                print(f"Error processing payment {payment.id}: {str(e)}")
                # Add a basic record even if there's an error
                export_record = {
                    "ID": payment.id or "",
                    "Username": "Error",
                    "Jumlah Pembayaran": 0,
                    "Metode Pembayaran": "",
                    "Status": "Error",
                    "Tanggal Pembayaran": "",
                    "ID Pembayaran": "",
                    "URL Pembayaran": ""
                }
                export_data.append(export_record)
        
        df = pd.DataFrame(export_data)
        
        if format == "excel":
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
                # First, write the DataFrame to create the worksheet
                df.to_excel(writer, index=False, sheet_name="Payments", startrow=7)
                
                # Now get the workbook and worksheet
                workbook = writer.book
                worksheet = writer.sheets["Payments"]
                
                # Define formats
                header_format = workbook.add_format({
                    'bold': True,
                    'font_size': 16,
                    'align': 'center',
                    'valign': 'vcenter',
                    'bg_color': '#4CAF50',
                    'font_color': 'white'
                })
                
                subheader_format = workbook.add_format({
                    'bold': True,
                    'font_size': 12,
                    'align': 'left',
                    'valign': 'vcenter'
                })
                
                info_format = workbook.add_format({
                    'font_size': 10,
                    'align': 'left',
                    'valign': 'vcenter'
                })
                
                # Add header information
                worksheet.merge_range('A1:H1', 'LAPORAN PEMBAYARAN IPL CANNART', header_format)
                worksheet.merge_range('A2:H2', '', info_format)  # Empty row
                
                # Add export information
                current_time = datetime.now().strftime("%d %B %Y %H:%M:%S")
                worksheet.merge_range('A3:H3', f'Periode: {start} s.d {end}', subheader_format)
                worksheet.merge_range('A4:H4', f'Dibuat pada: {current_time}', info_format)
                worksheet.merge_range('A5:H5', f'Dibuat oleh: System', info_format)
                worksheet.merge_range('A6:H6', f'Total Data: {len(export_data)} transaksi', info_format)
                worksheet.merge_range('A7:H7', '', info_format)  # Empty row
                
                # Adjust column widths
                worksheet.set_column('A:A', 15)  # ID
                worksheet.set_column('B:B', 15)  # Username
                worksheet.set_column('C:C', 18)  # Jumlah Pembayaran
                worksheet.set_column('D:D', 18)  # Metode Pembayaran
                worksheet.set_column('E:E', 12)  # Status
                worksheet.set_column('F:F', 20)  # Tanggal Pembayaran
                worksheet.set_column('G:G', 25)  # ID Pembayaran
                worksheet.set_column('H:H', 50)  # URL Pembayaran
                
            buffer.seek(0)
            return StreamingResponse(
                buffer,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={
                    "Content-Disposition": f'attachment; filename="Laporan_Pembayaran_IPL_Cannart_{start}_{end}.xlsx"',
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                    "Access-Control-Allow-Headers": "Content-Type, Authorization",
                },
            )
        else:
            return {"message": "PDF export not implemented for no-auth endpoint", "data": export_data}
            
    except Exception as e:
        print(f"Error in export_payments_no_auth: {str(e)}")
        return {"error": str(e), "message": "Export failed"}