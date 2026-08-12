import openpyxl
wb = openpyxl.load_workbook('excel/F003_GSW_TARI.xlsx')
ws = wb.active
print("Merged cell ranges:")
for r in list(ws.merged_cells.ranges):
    print(" -", r)
