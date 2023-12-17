import numpy as np
import pandas as pd


def parse_xls(filepath, sheet1, sheet2):
    """read xsens exported xls file

    Args:
        filepath (_type_): _description_
        sheet1 (_type_): _description_
        sheet2 (_type_): _description_

    Returns:
        _type_: _description_
    """
    # corresponding=[1,19,15,2,20,16,3,21,17,4,22,18,5,11,7,6,12,8,13,9,14,10,-1,-1]
    corresponding = [1, 20, 16, 3, 21, 17, 4, 22, 18, 5,
                     23, 19, 6, -1, -1, 7, 12, 8, 13, 9, 14, 10, 15, 11]
    sheet = pd.read_excel(filepath, sheet_name=None)
    bone_angles = sheet[sheet1].values[:, 1:]
    translation = sheet[sheet2].values[:, 1:]

    # kinematic tree angle 
    nframe, ncol = bone_angles.shape
    bone_angles_smpl = np.zeros(shape=(nframe, 24*3))
    for i in range(24):
        j = corresponding[i]-1
        if j >= 0:
            bone_angles_smpl[:, i*3:i*3+3] = bone_angles[:, j*3:j*3+3]

    # 模型平移
    translation_smpl = translation[:, :3]

    return bone_angles_smpl.astype(np.float32).reshape(nframe, -1, 3), translation_smpl.astype(np.float32)


if __name__ == "__main__":
    filepath = "data/nanling/test1-001-hd.xlsx"
    # Segment Orientation - Euler #Joint Angles XZY
    sheet1 = 'Segment Orientation - Euler'
    sheet2 = 'Center of Mass'
    p, t = parse_xls(filepath, sheet1, sheet2)

    # print(sheet.keys())
    # print(bone_angles.shape)
    # print(translation)
    # print(bone_angles.keys())
    print(p.shape)
    print(t.shape)
