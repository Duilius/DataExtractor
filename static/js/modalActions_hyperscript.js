// modalActions.hyperscript
alert("HyperScript cargado correctamente!")

def transferData()
    set codigoPrincipal to #input_principal_codigo
    set nombresPrincipal to #input_principal_nombres
    set gerenciaPrincipal to #input_principal_gerencia
    set fotoPrincipal to #input_principal_foto
    if codigoPrincipal exists
        put #codigo-seleccionado.value into codigoPrincipal.value
    end
    if nombresPrincipal exists
        put #nombres-seleccionado.value into nombresPrincipal.value
    end
    if gerenciaPrincipal exists
        put #gerencia-seleccionado.value into gerenciaPrincipal.value
    end
    if fotoPrincipal exists
        remove .oculto from fotoPrincipal
        put #foto-seleccionado.value into fotoPrincipal.src
    end
end

def resetSelection()
    put '' into #codigo-seleccionado.value
    put '' into #nombres-seleccionado.value
    put '' into #gerencia-seleccionado.value
    put '' into #foto-seleccionado.value
end

def closeModal()
    add .oculto to #aceptar-descartar
    remove .oculto from #lista-usuarios
    resetSelection()
    send modalClose to body
end
