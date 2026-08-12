import sys
print('python', sys.version)
import reporte
print('template_folder=', reporte.app.template_folder)
print('root_path=', reporte.app.root_path)
print('routes=', [r.rule for r in reporte.app.url_map.iter_rules()])