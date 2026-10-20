import sqlite3, os


def conexion():
    con = sqlite3.connect("Tienda.db")
    con.execute("PRAGMA foreign_keys = ON")
    return con


def mensajero(con):
    mensajero = con.cursor()
    return mensajero


def tabla(con):
    con.execute("""
    CREATE TABLE IF NOT EXISTS productos(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        precio REAL NOT NULL CHECK(precio >= 0),
        cantidad INTEGER NOT NULL CHECK(cantidad >= 0)
    )
    """)
    con.execute("""
    CREATE TABLE IF NOT EXISTS ventas(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        producto_id INTEGER NOT NULL,
        cantidad INTEGER NOT NULL CHECK(cantidad > 0),
        total REAL NOT NULL,
        fecha TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (producto_id) REFERENCES productos(id)
    )
    """)
    con.commit()


# ---------- utilidades ----------
def pausa():
    input("Presione Enter para continuar...")


def pedir_entero(mensaje):
    while True:
        try:
            return int(input(mensaje))
        except ValueError:
            print("Porfavor ingrese un numero entero valido")


def pedir_decimal(mensaje):
    while True:
        try:
            return float(input(mensaje))
        except ValueError:
            print("Porfavor ingrese un numero valido")


def buscar_producto(cursor, id_producto):
    cursor.execute("SELECT id, nombre, precio, cantidad FROM productos WHERE id = ?", (id_producto,))
    return cursor.fetchone()


# ---------- menu ----------
def main():
    base_datos = conexion()
    cursor = mensajero(base_datos)
    tabla(base_datos)
    try:
        while True:
            os.system("cls")
            print("menu")
            print("1. Registrar producto")
            print("2. Ver productos")
            print("3. Actualizar producto")
            print("4. Eliminar producto")
            print("5. Registrar venta")
            print("6. Historial de ventas")
            print("7. Demostrar rollback (error controlado)")
            print("8. Salir")

            try:
                opcion = int(input("Eliga una opcion del menu: "))
            except ValueError:
                opcion = 0

            match opcion:
                case 1:
                    registrar_producto(cursor, base_datos)
                case 2:
                    mostrar_productos(cursor)
                case 3:
                    actualizar_producto(cursor, base_datos)
                case 4:
                    eliminar_producto(cursor, base_datos)
                case 5:
                    registrar_venta(cursor, base_datos)
                case 6:
                    mostrar_historial(cursor)
                case 7:
                    demostrar_rollback(cursor, base_datos)
                case 8:
                    print("saliendo...")
                    break
                case _:
                    print("Porfavor eliga una opcion valida!!")
                    pausa()
                    continue

    except Exception as e:
        base_datos.rollback()
        print(f"ERROR,{e}, no hubo ningun cambios")
        print("saliendo...")
    finally:
        base_datos.close()


# ---------- CRUD de productos ----------
def registrar_producto(cursor, bd):
    while True:
        nombre = input("Nombre del producto: ").strip()
        if nombre == "":
            print("El nombre no puede estar vacio")
            pausa()
            continue
        break
    while True:
        precio = pedir_decimal("Precio: ")
        cantidad = pedir_entero("Cantidad disponible: ")
        if precio < 0 or cantidad < 0:
            print("El precio y la cantidad no pueden ser negativos")
            pausa()
            continue
        break
    try:
        cursor.execute(
            "INSERT INTO productos (nombre,precio,cantidad) VALUES (?,?,?)",
            (nombre, precio, cantidad),
        )
    except Exception as error:
        bd.rollback()
        print(f"ERROR, {error}, no hubo ningun cambio")
    else:
        bd.commit()
        print("Producto guardado con exito")
    pausa()


def mostrar_productos(cursor):
    cursor.execute("SELECT id, nombre, precio, cantidad FROM productos")
    lista = cursor.fetchall()
    if not lista:
        print("No hay productos")
    else:
        print("Productos")
        for producto in lista:
            print(f"id: {producto[0]} | Nombre: {producto[1]} | Precio: {producto[2]} | Cantidad: {producto[3]}")
    pausa()


def actualizar_producto(cursor, bd):
    while True:
        id_buscar = pedir_entero("Ingrese la id del producto a actualizar: ")
        producto = buscar_producto(cursor, id_buscar)
        if producto is None:
            print("No hay ningun producto con ese id")
            pausa()
            continue
        break
    print(f"Producto: {producto[1]} | Precio: {producto[2]} | Cantidad: {producto[3]}")
    print("1. Actualizar precio")
    print("2. Actualizar cantidad")
    while True:
        opcion = pedir_entero("Que desea actualizar: ")
        try:
            match opcion:
                case 1:
                    while True:
                        nuevo_precio = pedir_decimal("Nuevo precio: ")
                        if nuevo_precio < 0:
                            print("El precio no puede ser negativo")
                            pausa()
                            continue
                        break
                    cursor.execute("UPDATE productos SET precio = ? WHERE id = ?", (nuevo_precio, id_buscar))
                case 2:
                    while True:
                        nueva_cantidad = pedir_entero("Nueva cantidad: ")
                        if nueva_cantidad < 0:
                            print("La cantidad no puede ser negativa")
                            pausa()
                            continue
                        break
                    cursor.execute("UPDATE productos SET cantidad = ? WHERE id = ?", (nueva_cantidad, id_buscar))
                case _:
                    print("Opcion no valida")
                    pausa()
                    continue
        except Exception as error:
            bd.rollback()
            print(f"ERROR, {error}, no hubo ningun cambio")
        else:
            bd.commit()
            print("Producto actualizado con exito")
        pausa()
        break


def eliminar_producto(cursor, bd):
    while True:
        id_buscar = pedir_entero("Ingrese la id del producto a eliminar: ")
        producto = buscar_producto(cursor, id_buscar)
        if producto is None:
            print("No hay ningun producto con ese id")
            pausa()
            continue
        break
    while True:
        confirmar = input(f"Seguro que desea eliminar '{producto[1]}'? S/N ").lower().strip()
        if confirmar == "s":
            print("Entendido realizando cambios...")
            break
        elif confirmar == "n":
            print("No se elimino nada")
            pausa()
            break
        else:
            print("Ingrese una respuesta valida")
    if confirmar == "n":
        return
    try:
        cursor.execute("DELETE FROM productos WHERE id = ?", (id_buscar,))
    except sqlite3.IntegrityError:
        # el producto ya tiene ventas asociadas, la clave foranea lo protege
        bd.rollback()
        print("No se puede eliminar: el producto tiene ventas registradas")
    except Exception as error:
        bd.rollback()
        print(f"ERROR, {error}, no hubo ningun cambio")
    else:
        bd.commit()
        print("Producto eliminado con exito")
    pausa()


# ---------- ventas ----------
def registrar_venta(cursor, bd):
    id_producto = pedir_entero("Ingrese la id del producto a vender: ")
    cantidad = pedir_entero("Ingrese la cantidad a vender: ")
    ejecutar_venta(cursor, bd, id_producto, cantidad)
    pausa()

def ejecutar_venta(cursor, bd, id_producto, cantidad, forzar_error=False):
    # 1. validaciones antes de tocar la base de datos
    producto = buscar_producto(cursor, id_producto)
    if producto is None:
        print("No existe un producto con ese id")
        return False
    if cantidad <= 0:
        print("La cantidad debe ser mayor a 0")
        return False
    if cantidad > producto[3]:
        print(f"Stock insuficiente. Disponible: {producto[3]}")
        return False

    total = producto[2] * cantidad

    # 2. transaccion: o se hacen las dos operaciones o no se hace ninguna
    try:
        cursor.execute(
            "INSERT INTO ventas (producto_id,cantidad,total) VALUES (?,?,?)",
            (id_producto, cantidad, total),
        )
        if forzar_error:
            raise Exception("Error simulado despues de registrar la venta")
        cursor.execute(
            "UPDATE productos SET cantidad = cantidad - ? WHERE id = ?",
            (cantidad, id_producto),
        )
    except Exception as error:
        bd.rollback()
        print(f"ERROR, {error}")
        print("Se cancelo toda la operacion (rollback)")
        return False
    else:
        bd.commit()
        print(f"Venta registrada con exito. Total: {total}")
        return True


def mostrar_historial(cursor):
    cursor.execute("""
    SELECT ventas.id, productos.nombre, ventas.cantidad, ventas.total, ventas.fecha
    FROM ventas
    INNER JOIN productos ON ventas.producto_id = productos.id
    ORDER BY ventas.id
    """)
    lista = cursor.fetchall()
    if not lista:
        print("No hay ventas registradas")
    else:
        print("Historial de ventas")
        for venta in lista:
            print(f"venta: {venta[0]} | Producto: {venta[1]} | Cantidad: {venta[2]} | Total: {venta[3]} | Fecha: {venta[4]}")
    pausa()


def demostrar_rollback(cursor, bd):
    id_producto = pedir_entero("Id del producto para la prueba: ")
    producto = buscar_producto(cursor, id_producto)
    if producto is None:
        print("No existe un producto con ese id")
        pausa()
        return
    cantidad = pedir_entero("Cantidad a vender en la prueba: ")

    stock_antes = producto[3]
    cursor.execute("SELECT COUNT(*) FROM ventas")
    ventas_antes = cursor.fetchone()[0]
    print(f"ANTES   -> stock: {stock_antes} | ventas registradas: {ventas_antes}")

    ejecutar_venta(cursor, bd, id_producto, cantidad, forzar_error=True)

    stock_despues = buscar_producto(cursor, id_producto)[3]
    cursor.execute("SELECT COUNT(*) FROM ventas")
    ventas_despues = cursor.fetchone()[0]
    print(f"DESPUES -> stock: {stock_despues} | ventas registradas: {ventas_despues}")

    if stock_antes == stock_despues and ventas_antes == ventas_despues:
        print("Los datos permanecen intactos")
    else:
        print("Los datos cambiaron, algo salio mal")
    pausa()


if __name__ == "__main__":
    main()