import openpyxl
wb = openpyxl.load_workbook('excel/Tarifas_J.xlsx')
ws = wb.active
print("Merged cell ranges:")
for r in list(ws.merged_cells.ranges):
    print(" -", r)
