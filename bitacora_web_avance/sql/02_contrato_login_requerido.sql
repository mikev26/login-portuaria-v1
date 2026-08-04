/*
ESTE ARCHIVO NO CREA EL LOGIN.
Documenta el contrato que Django necesita consumir.

Ejemplo esperado (los nombres reales pueden cambiar):

EXEC op_claves.dbo.sp_validar_usuario
    @usuario = 'jmacias',
    @clave = '********';

Con credenciales correctas debería devolver una fila parecida a:

idusuario | usuario  | nombre                         | cargo                                      | autorizado
48        | jmacias  | Macias Vera Jonathan Alexander | Inspector del Terminal Pesquero y Cabotaje | 1

Con credenciales incorrectas puede:
- no devolver filas, o
- devolver autorizado = 0.

IMPORTANTE:
Django no debe descifrar, comparar ni almacenar contraseñas directamente.
Debe consumir el procedimiento institucional que ya aplique el método correcto
(hash, cifrado o validación interna) en la base op_claves.
*/
