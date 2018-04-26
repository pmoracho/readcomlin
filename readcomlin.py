# -*- coding: utf-8 -*-
#
# vim: sw=4:expandtab:foldmethod=marker
#
# Copyright (c) 2018 Patricio Moracho <pmoracho@gmail.com>
#
# readcomlin
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of version 3 of the GNU General Public License
# as published by the Free Software Foundation. A copy of this license should
# be included in the file GPL-3.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Library General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.

__author__      = "Patricio Moracho <pmoracho@gmail.com>"
__appname__     = "readcomlin"
__appdesc__     = "Extración de datos de los PDF de comprobantes en línea"
__license__     = 'GPL v3'
__copyright__   = "2018 %s" % (__author__)
__version__     = "1.0.1"
__date__        = "2018/04/20"

###############################################################################
# Imports
###############################################################################
try:
    import sys
    import os
    import gettext
    import importlib
    from gettext import gettext as _
    gettext.textdomain('padrondl')

    def _my_gettext(s):
        """my_gettext: Traducir algunas cadenas de argparse."""
        current_dict = {
            'usage: ': 'uso: ',
            'optional arguments': 'argumentos opcionales',
            'show this help message and exit': 'mostrar esta ayuda y salir',
            'positional arguments': 'argumentos posicionales',
            'the following arguments are required: %s': 'los siguientes argumentos son requeridos: %s',
            'show program''s version number and exit': 'Mostrar la versión del programa y salir',
            'expected one argument': 'se espera un valor para el parámetro',
            'expected at least one argument': 'se espera al menos un valor para el parámetro'
        }

        if s in current_dict:
            return current_dict[s]
        return s

    gettext.gettext = _my_gettext

    """
    Librerias adicionales
    """
    import argparse
    import re
    from PyPDF2 import PdfFileWriter, PdfFileReader

except ImportError as err:
    modulename = err.args[0].split()[3]
    print("No fue posible importar el modulo: %s" % modulename)
    sys.exit(-1)



##################################################################################################################################################
# Inicializar parametros del programa
##################################################################################################################################################
def init_argparse():
    """Inicializar parametros del programa."""

    usage = '\nEjemplos de uso:\n\n' \
            '- Recuperar datos de un archivo PDF generado por la factura online del Afip\n' \
            '  %(prog)s <archivo pdf>\n\n' \
            '- Mostrar esta ayuda:\n' \
            '  %(prog)s -h\n\n'

    cmdparser = argparse.ArgumentParser(prog=__appname__,
                                        description="%s\n%s\n" % (__appdesc__, __copyright__),
                                        epilog=usage,
                                        add_help=True,
                                        formatter_class=lambda prog: argparse.RawTextHelpFormatter(prog, max_help_position=35)
    )

    opciones = {    "inputfile": {
                                "type": str,
                                "nargs": '?',
                                "action": "store",
                                "help": _("Archivo PDF a procesar")
                    },
                    "--version -v": {
                                "action":   "version",
                                "version":  __version__,
                                "help":     _("Mostrar el número de versión y salir")
                    },
                    "--output-file -o": {
                                "type":     str,
                                "action":   "store",
                                "dest":     "outputfile",
                                "default":  None,
                                "help":     _("Generar la salida en un archivo determinado")
                    },
                    "--to-text -t": {
                                "action":   "store_true",
                                "dest":     "totext",
                                "default":  False,
                                "help":     _("Extraer la información de un PDF")
                    },
                    "--log-level -n": {
                                "type":     str,
                                "action":   "store",
                                "dest":     "loglevel",
                                "default":  "info",
                                "help":     _("Nivel de log")
                    },
            }

    for key, val in opciones.items():
        args = key.split()
        kwargs = {}
        kwargs.update(val)
        cmdparser.add_argument(*args, **kwargs)

    return cmdparser


def showerror(msg):
    print("\n!!!! [%s] error: %s\n" % (__appname__, msg))

def expand_filename(filename):
    """Expansión de nombre de archivo con ciertos keywords especiales

    Args:
        filename (str): Nombre de archivo

    Example:

        >>> expand_filename('{desktop}/salida.txt') # Expande el nombre al escritorio del usuario
        >>> expand_filename('{tmpdir}/salida.txt')  # Expande el nombre a una carpeta temporal
        >>> expand_filename('{tmpdir}/{tmpfile}')   # Expande el nombre a una carpeta y archivo temporal
    """

    if '{desktop}' in filename:
        print(filename)
        tmp = os.path.join(os.path.expanduser('~'), 'Desktop')
        print(tmp)
        filename = filename.replace('{desktop}', tmp)

    if '{tmpdir}' in filename:
        tmp = tempfile.gettempdir()
        filename = filename.replace('{tmpdir}', tmp)

    if '{tmpfile}' in filename:
        tmp = tempfile.mktemp()
        filename = filename.replace('{tmpfile}', tmp)

    return filename

def load_plugins(plug_path):
    """Carga las clases de los formatos a procesar definidas
    prviamente en la carpeta de "plugins"
    """

    pysearchre = re.compile('^pdf_data_.+\.py$', re.IGNORECASE)
    pluginfiles = filter(pysearchre.search,
                         os.listdir(os.path.join(os.path.dirname(__file__),plug_path)))

    form_module = lambda fp: '.' + os.path.splitext(fp)[0]
    plugins = map(form_module, pluginfiles)

    importlib.import_module('plugins')
    modules = []
    for plugin in plugins:
        if not plugin.startswith('__'):
            m = importlib.import_module(plugin, package="plugins")
            o = getattr(m, "PDF_DATA")
            if o:
                modules.append(o())

    return modules


def get_pdf_data(filename, formatos):

    with open(filename, "rb") as f:
        pdf = PdfFileReader(f,strict=False)
        for page in pdf.pages:
            p = page.extractText()
            for f in formatos:
                m = re.search(f.patron, p)
                if m:
                    return(f.get_data(m,p))
    return None

def get_pdf_totext(filename, formatos):

    with open(filename, "rb") as f:
        pdf = PdfFileReader(f,strict=False)
        p = ""
        for page in pdf.pages:
            p = p + page.extractText()
        return p

    return None

##################################################################################################################################################
# Main program
##################################################################################################################################################
if __name__ == "__main__":

    cmdparser = init_argparse()
    try:
        args = cmdparser.parse_args()
    except IOError as msg:
        cmdparser.error(str(msg))
        sys.exit(-1)

    if args.inputfile:
        try:
            formatos = load_plugins("plugins")
            if not args.totext:
                data = get_pdf_data(args.inputfile, formatos)
            else:
                data = get_pdf_totext(args.inputfile, formatos)

            if args.outputfile:
                with open(expand_filename(args.outputfile), "wt") as f:
                    f.write(str(data))
            else:
                print(data)

        except FileNotFoundError as e:
            showerror("Imposible leer {}, verifique que exista y sea un archivo PDF válido".format(args.inputfile))
            sys.exit(-1)

    else:
        showerror("No se ha indicado el archivo PDF a procesar")
        cmdparser.print_help()
        sys.exit(-1)
