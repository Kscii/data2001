import pandas as pd

# xfan0282
def extract_unit_column(df: pd.DataFrame) -> pd.DataFrame:

    df = df.copy()

    # 同时兼容clean_column_names执行前和执行后的列名
    desc_col = "description" if "description" in df.columns else "Description"
    desc = df[desc_col].astype(str)

    # 提取description末尾括号中的单位
    extracted = desc.str.extract(r"\s*\(([^)]+)\)\s*$", expand=False)
    has_bracket = extracted.notna()

    # 移除末尾括号及其中内容，得到纯描述文本
    stripped_desc = desc.str.replace(r"\s*\([^)]+\)\s*$", "", regex=True).str.strip()

    # 对于部分没有末尾括号的特殊规则
    no_bracket = ~has_bracket
    inferred = pd.Series(pd.NA, index=df.index, dtype=object)

    # Total number of 和 Number of 转换为 no.
    inferred[no_bracket & desc.str.match(r"^(?:Number of|Total number of)\b", case=False)] = "no."
    # Census - Count of 转换为 no.
    inferred[no_bracket & desc.str.match(r"^Census\s*-\s*Count of\b", case=False)] = "no."
    # 以 % 开头的转换为 %
    inferred[no_bracket & desc.str.startswith("%")] = "%"

    # 合并结果并归一化
    unit = extracted.where(has_bracket, inferred)
    unit = unit.replace({"no. of persons": "no."})

    df[desc_col] = stripped_desc.where(has_bracket, desc)
    df["unit"] = unit

    # 返回dataframe对象
    return df
