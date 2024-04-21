def determinar_tipo_dispositivo(ancho_pantalla):
    breakpoint_mobile = 600
    breakpoint_tablet = 1000

    print("ANCHO PANTALLA =============> ", ancho_pantalla)
    #ancho_pantalla = int(ancho_pantalla)

    if ancho_pantalla < breakpoint_mobile:
        return "mobile"
    elif ancho_pantalla < breakpoint_tablet:
        return "tablet"
    else:
        return "desktop"
