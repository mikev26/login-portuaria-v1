"""Servicio para la generación de reportes PDF y envío de correos electrónicos."""

from __future__ import annotations

import logging
from typing import Any

from django.conf import settings
from django.core.mail import EmailMessage

from .pdf_inflacion import generar_pdf_tarifario_inflacion

logger = logging.getLogger(__name__)


def enviar_correo_ajuste_inflacion(
    porcentaje: float,
    anio: int,
    fecha_inflacion: str,
    detalle: str = "",
    usuario_nombre: str = "Usuario",
    tarifas: list[dict[str, Any]] | None = None,
) -> bool:
    """Genera el PDF oficial de inflación y lo envía por correo electrónico a los destinatarios configurados."""
    destinatarios = getattr(settings, "EMAIL_DESTINATARIOS_INFLACION", [])
    if not destinatarios:
        logger.info("No hay destinatarios configurados en EMAIL_DESTINATARIOS_INFLACION. Se omite el envío de correo.")
        return False

    if not getattr(settings, "EMAIL_HOST_USER", None) or not getattr(settings, "EMAIL_HOST_PASSWORD", None):
        logger.warning("No se han configurado EMAIL_HOST_USER o EMAIL_HOST_PASSWORD en .env / settings. Se omite el envío de correo.")
        return False

    try:
        lista_tarifas = tarifas if tarifas is not None else []
        
        # Generamos los bytes del PDF oficial
        pdf_bytes = generar_pdf_tarifario_inflacion(
            tarifas=lista_tarifas,
            anio=anio,
            porcentaje=porcentaje,
            fecha_inflacion=fecha_inflacion,
            detalle=detalle,
        )

        asunto = f"Notificación Oficial: Ajuste Tarifario por Inflación {anio} ({porcentaje:.2f}%)"
        
        cuerpo = f"""Estimados,

Se ha registrado exitosamente el proceso de ajuste tarifario por inflación anual para el año fiscal {anio}.

• Porcentaje de Inflación aplicado: {porcentaje:.2f} %
• Fecha de Aplicación: {fecha_inflacion}
• Justificación / Detalle: {detalle if detalle else 'Sin observaciones'}
• Registrado por: {usuario_nombre}

Adjunto a este correo encontrarán el documento oficial en formato PDF con el tarifario actualizado.

Atentamente,
Autoridad Portuaria de Manta
Sistema de Bitácora y Tarifario Portuario
"""

        remitente = getattr(settings, "DEFAULT_FROM_EMAIL", settings.EMAIL_HOST_USER)

        email = EmailMessage(
            subject=asunto,
            body=cuerpo,
            from_email=remitente,
            to=destinatarios,
        )

        nombre_archivo = f"Tarifario_Inflacion_{anio}_{fecha_inflacion}.pdf"
        email.attach(
            filename=nombre_archivo,
            content=pdf_bytes,
            mimetype="application/pdf",
        )

        email.send(fail_silently=False)
        logger.info("Correo de ajuste de inflación enviado exitosamente a: %s", destinatarios)
        return True
    except Exception as exc:
        logger.exception("Error al enviar el correo de ajuste de inflación: %s", exc)
        return False
