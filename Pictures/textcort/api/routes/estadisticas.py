from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, date
from database import get_db
from api.routes.auth import get_current_admin
from models.venta import Venta, DetalleVenta
from models.gasto import Gasto
from models.producto import Producto
from models.usuario import Usuario

router = APIRouter()

@router.get("/dashboard")
def estadisticas_dashboard(
    current_user = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Estadísticas generales para el dashboard"""
    hoy = date.today()
    
    # Ventas de hoy
    ventas_hoy = db.query(Venta).filter(
        func.date(Venta.fecha) == hoy
    ).all()
    
    # Total ventas del día
    total_ventas_hoy = sum(v.total for v in ventas_hoy) if ventas_hoy else 0
    
    # Gastos de hoy
    gastos_hoy = db.query(Gasto).filter(
        func.date(Gasto.fecha) == hoy
    ).all()
    
    total_gastos_hoy = sum(g.monto for g in gastos_hoy) if gastos_hoy else 0
    
    # Totales generales
    total_ventas = db.query(func.sum(Venta.total)).scalar() or 0
    total_gastos = db.query(func.sum(Gasto.monto)).scalar() or 0
    total_productos = db.query(func.count(Producto.id)).scalar() or 0
    total_usuarios = db.query(func.count(Usuario.id)).scalar() or 0
    
    # Productos con stock bajo
    productos_stock_bajo = db.query(Producto).filter(Producto.stock < 10).count()
    
    return {
        "ventas_hoy": {
            "cantidad": len(ventas_hoy),
            "total": round(total_ventas_hoy, 2)
        },
        "gastos_hoy": {
            "cantidad": len(gastos_hoy),
            "total": round(total_gastos_hoy, 2)
        },
        "neto_hoy": round(total_ventas_hoy - total_gastos_hoy, 2),
        "totales": {
            "ventas": round(total_ventas, 2),
            "gastos": round(total_gastos, 2),
            "neto": round(total_ventas - total_gastos, 2),
            "productos": total_productos,
            "usuarios": total_usuarios
        },
        "alertas": {
            "productos_stock_bajo": productos_stock_bajo
        }
    }

@router.get("/ventas-recientes")
def ventas_recientes(
    limit: int = Query(10, le=50),
    current_user = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Últimas ventas realizadas"""
    ventas = db.query(Venta).order_by(Venta.fecha.desc()).limit(limit).all()
    
    return [
        {
            "id": v.id,
            "total": round(v.total, 2),
            "fecha": v.fecha,
            "usuario": v.usuario.username if v.usuario else "Invitado",
            "cantidad_productos": len(v.detalles)
        }
        for v in ventas
    ]

@router.get("/grafico-ventas-mes")
def grafico_ventas_mes(
    current_user = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Datos para gráfico de ventas del mes actual"""
    hoy = date.today()
    primer_dia = date(hoy.year, hoy.month, 1)
    
    datos = db.query(
        func.date(Venta.fecha).label('fecha'),
        func.sum(Venta.total).label('total')
    ).filter(
        Venta.fecha >= primer_dia
    ).group_by(func.date(Venta.fecha)).all()
    
    return [
        {
            "fecha": d[0].isoformat(),
            "total": round(d[1], 2)
        }
        for d in datos
    ]
