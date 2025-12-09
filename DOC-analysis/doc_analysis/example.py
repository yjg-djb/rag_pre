# 以下是优化后的表格处理相关代码，主要修改了extract_table_text函数
# 并新增了处理XML表格结构的辅助函数

def parse_cell_text(cell_elem):
    """解析单元格内的文本内容，处理多行文本"""
    texts = []
    for para in cell_elem.iterfind('.//w:p', namespaces=cell_elem.nsmap):
        para_text = ''.join(
            run.text for run in para.iterfind('.//w:t', namespaces=cell_elem.nsmap) if run.text
        ).strip()
        if para_text:
            texts.append(para_text)
    return '\n'.join(texts)


def is_header_row(row_elem):
    """判断行是否为表头行"""
    # 检查行内是否有表头标记或样式
    for cell in row_elem.iterfind('.//w:tc', namespaces=row_elem.nsmap):
        for p in cell.iterfind('.//w:p', namespaces=cell.elem.nsmap):
            p_pr = p.find('.//w:pPr', namespaces=p.nsmap)
            if p_pr is not None:
                p_style = p_pr.find('.//w:pStyle', namespaces=p_pr.nsmap)
                if p_style is not None and p_style.get(qn('w:val')) == '表头':
                    return True
    # 检查表格是否有表头定义
    tbl = row_elem.getparent()
    tbl_pr = tbl.find('.//w:tblPr', namespaces=tbl.nsmap)
    if tbl_pr is not None:
        tbl_header = tbl_pr.find('.//w:tblHeader', namespaces=tbl_pr.nsmap)
        if tbl_header is not None:
            return True
    return False


def process_merged_cells(table_elem):
    """处理合并单元格，构建完整表格数据"""
    nsmap = table_elem.nsmap
    rows = list(table_elem.iterfind('.//w:tr', namespaces=nsmap))
    if not rows:
        return []

    # 获取表格列数
    grid_cols = table_elem.find('.//w:tblGrid/w:gridCol', namespaces=nsmap)
    if grid_cols is None:
        cols_count = max(len(list(row.iterfind('.//w:tc', namespaces=nsmap))) for row in rows)
    else:
        cols_count = len(table_elem.findall('.//w:tblGrid/w:gridCol', namespaces=nsmap))

    # 初始化表格矩阵
    table_data = []
    merged_cells = []  # 记录合并单元格信息 (row, col, width, height, value)

    for row_idx, row in enumerate(rows):
        row_data = []
        cells = list(row.iterfind('.//w:tc', namespaces=nsmap))
        col_idx = 0

        # 跳过已被合并的单元格
        while any(m[0] == row_idx and m[1] == col_idx for m in merged_cells):
            col_idx += 1
            if col_idx >= cols_count:
                break

        for cell in cells:
            if col_idx >= cols_count:
                break

            # 检查是否为合并单元格
            grid_span = cell.find('.//w:tcPr/w:gridSpan', namespaces=nsmap)
            v_merge = cell.find('.//w:tcPr/w:vMerge', namespaces=nsmap)

            col_span = int(grid_span.get(qn('w:val'))) if grid_span is not None else 1
            row_span = 1

            # 处理行合并
            if v_merge is not None:
                v_merge_val = v_merge.get(qn('w:val'))
                if v_merge_val == 'restart':
                    # 查找合并的行数
                    current_row = row_idx + 1
                    while current_row < len(rows):
                        next_cell = None
                        # 查找下一行中对应位置的单元格
                        next_row_cells = list(rows[current_row].iterfind('.//w:tc', namespaces=nsmap))
                        temp_col = col_idx
                        cell_count = 0
                        for c in next_row_cells:
                            c_span = int(c.find('.//w:tcPr/w:gridSpan', namespaces=nsmap).get(qn('w:val'))) if c.find(
                                './/w:tcPr/w:gridSpan', namespaces=nsmap) is not None else 1
                            if temp_col < cell_count + c_span:
                                next_cell = c
                                break
                            cell_count += c_span

                        if next_cell is not None and next_cell.find('.//w:tcPr/w:vMerge', namespaces=nsmap) is not None:
                            row_span += 1
                            current_row += 1
                        else:
                            break
                    merged_cells.append((row_idx, col_idx, col_span, row_span, parse_cell_text(cell)))

            # 填充单元格内容
            cell_text = parse_cell_text(cell)
            row_data.append(cell_text)

            # 处理列合并，填充空内容
            for i in range(1, col_span):
                if col_idx + i < cols_count:
                    row_data.append('')

            # 更新列索引
            col_idx += col_span

            # 跳过已被合并的单元格
            while any(m[0] == row_idx and m[1] == col_idx for m in merged_cells):
                row_data.append('')
                col_idx += 1
                if col_idx >= cols_count:
                    break

        # 补充行尾可能缺失的单元格
        while len(row_data) < cols_count:
            row_data.append('')

        table_data.append(row_data)

    # 填充合并单元格的内容
    for (start_row, start_col, width, height, value) in merged_cells:
        for i in range(height):
            for j in range(width):
                if start_row + i < len(table_data) and start_col + j < len(table_data[start_row + i]):
                    table_data[start_row + i][start_col + j] = value

    return table_data


def extract_table_text(docx_path: Path) -> list:
    """优化后的表格提取函数，通过解析XML处理合并单元格和表头"""
    try:
        doc = Document(docx_path)
        table_texts = []

        for table in doc.tables:
            # 获取底层XML元素
            table_elem = table._element
            table_data = process_merged_cells(table_elem)

            if not table_data:
                continue

            # 识别表头行
            header_rows = []
            data_rows = []
            for i, row in enumerate(table_data):
                if is_header_row(table_elem[i]):  # table_elem[i] 是第i行的XML元素
                    header_rows.append(row)
                else:
                    data_rows.append(row)

            # 处理无表头的情况
            if not header_rows:
                header_rows = [table_data[0]]
                data_rows = table_data[1:] if len(table_data) > 1 else []

            # 格式化输出
            formatted_table = []
            if header_rows:
                # 合并可能存在的多行表头
                headers = []
                for header_row in header_rows:
                    for i, header in enumerate(header_row):
                        if i < len(headers):
                            headers[i] = f"{headers[i]} {header}".strip()
                        else:
                            headers.append(header.strip())

                # 处理数据行
                for row in data_rows:
                    row_str = []
                    for i, (header, value) in enumerate(zip(headers, row)):
                        if header:  # 只有表头存在时才添加键值对格式
                            row_str.append(f"{header}: {value}" if value else f"{header}: ")
                        else:
                            row_str.append(value)
                    if row_str:
                        formatted_table.append(", ".join(row_str))
            else:
                # 无表头表格直接拼接
                for row in table_data:
                    if any(cell.strip() for cell in row):
                        formatted_table.append(", ".join(row))

            if formatted_table:
                table_texts.append("\n".join(formatted_table))

        return table_texts
    except Exception as e:
        logger.error(f"表格提取失败 {docx_path.name}: {str(e)}")
        return []