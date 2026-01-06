import math  # Cần cho sqrt()

# ====== Bộ tiêu chuẩn môi trường (dành cho cây bần chua - vùng biển ven bờ) ======
standards = {
    'nhiet_do_kk': (22, 27),
    'luong_mua': (1500, 3000),
    'ph': (6.5, 8.5),
    'do_man': (5, 20),
    'do_kiem': (60, 180),
    'nh3': (0, 0.3),
    'h2s': (0, 0.05),
    'nhiet_do_nuoc_bien': (18, 28),
    'bod5': (0, 50),
    'cod': (0, 150),
    'tss': (0, 50),
    'as': (0, 12),
    'cd': (0, 2),
    'pb': (0, 100),
    'cu': (0, 70),
    'zn': (0, 200)
}

# Trọng số cuối cùng
weights = {
    'nhiet_do_kk': 0.5,
    'luong_mua': 0.5,
    'ph': 2.5,
    'do_man': 2.5,
    'do_kiem': 1.0,
    'nh3': 2.5,
    'h2s': 2.5,
    'nhiet_do_nuoc_bien': 0.8,
    'bod5': 1.5,
    'cod': 1.5,
    'tss': 1.0,
    'as': 3.0,
    'cd': 3.0,
    'pb': 2.5,
    'cu': 2.0,
    'zn': 2.0
}

# Các thông số thuộc loại "khoảng lý tưởng"
range_params = [
    'nhiet_do_kk',
    'luong_mua',
    'ph',
    'do_man',
    'do_kiem',
    'nhiet_do_nuoc_bien'
]


def calculate_eai(measured_data: dict) -> dict:
    """
    Tính Environmental Assessment Index (EAI) theo biến thể Nemerow (không chuẩn hóa về 0-100).
    EAI càng gần/thấp hơn 1 → môi trường càng tốt/an toàn.
    """
    if not measured_data:
        return {"error": "Không có dữ liệu đo nào được cung cấp."}

    # Bước 1: Tính SI_i
    si_values = {}
    sub_assessment = {}

    for param, value in measured_data.items():
        if param not in standards:
            continue
        if value is None or not isinstance(value, (int, float)):
            continue

        l, u = standards[param]

        if param in range_params:
            m = (l + u) / 2
            r = (u - l) / 2
            si = abs(value - m) / r if r > 0 else 0.0
        else:
            si = value / u if u > 0 else 0.0

        si_values[param] = si

        # Phân mức cảnh báo SI_i (giữ nguyên)
        if si <= 0.5:
            level = "Rất tốt / Lý tưởng"
            color = "Xanh đậm"
        elif si <= 1.0:
            level = "An toàn"
            color = "Xanh nhạt"
        elif si <= 1.5:
            level = "Cảnh báo / Nguy hiểm nhẹ"
            color = "Vàng"
        elif si <= 3.0:
            level = "Nguy hiểm trung bình"
            color = "Cam"
        else:
            level = "Nguy hiểm cao"
            color = "Đỏ"

        sub_assessment[param] = {
            "value": value,
            "si": round(si, 3),
            "level": level,
            "color": color
        }

    k = len(si_values)
    if k < 4:
        return {
            "warning": "Không đủ dữ liệu (cần ít nhất 4 thông số để tính EAI đáng tin cậy)",
            "num_params_used": k,
            "sub_assessment": sub_assessment
        }

    # Bước 2: Tổng hợp EAI theo biến thể Nemerow
    sum_w_si = 0.0
    sum_w = 0.0
    si_max = max(si_values.values())

    for param, si in si_values.items():
        w = weights.get(param, 1.0)
        sum_w_si += si * w
        sum_w += w

    if sum_w == 0:
        return {"error": "Tổng trọng số bằng 0."}

    si_w_avg = sum_w_si / sum_w

    # EAI = EAI_raw (theo Nemerow) – không chuẩn hóa về 0-100
    eai = math.sqrt(((si_max ** 2) + (si_w_avg ** 2)) / 2)

    # Phân loại mức độ dựa trực tiếp trên EAI (càng gần/thấp hơn 1 càng tốt)
    if eai <= 1.0:
        eai_level = "Rất an toàn / Tuyệt hảo"
        eai_color = "Xanh dương"
    elif eai <= 1.2:
        eai_level = "An toàn tốt"
        eai_color = "Xanh lá"
    elif eai <= 1.5:
        eai_level = "Trung bình (cần theo dõi)"
        eai_color = "Vàng"
    elif eai <= 2.0:
        eai_level = "Không an toàn / Xấu"
        eai_color = "Cam"
    else:
        eai_level = "Nguy hiểm cao (cần xử lý khẩn cấp)"
        eai_color = "Đỏ"

    return {
        "EAI": round(eai, 3),
        "eai_level": eai_level,
        "eai_color": eai_color,
        "si_max": round(si_max, 3),
        "si_w_avg": round(si_w_avg, 3),
        "num_params_used": k,
        "sub_assessment": sub_assessment,
        "note": "EAI dựa trực tiếp trên Nemerow (càng gần/thấp hơn 1 càng tốt)"
    }


if __name__ == "__main__":

    test_cases = {
        "CASE 1 – Sinh thái tốt": {
            'ph': 7.5, 'do_man': 10, 'luong_mua': 2000,
            'nh3': 0.05, 'h2s': 0.005, 'nhiet_do_nuoc_bien': 25,
            'bod5': 5, 'as': 2, 'cd': 0.1,
        },

        "CASE 2 – Hơi rủi ro": {
            'ph': 6.8, 'do_man': 18, 'luong_mua': 2800,
            'nh3': 0.25, 'h2s': 0.015, 'nhiet_do_nuoc_bien': 28,
            'bod5': 12, 'as': 5, 'cd': 0.3,
        },

        "CASE 3 – Ô nhiễm trung bình": {
            'ph': 6.5, 'do_man': 22, 'luong_mua': 3200,
            'nh3': 0.5, 'h2s': 0.03, 'nhiet_do_nuoc_bien': 30,
            'bod5': 25, 'as': 8, 'cd': 0.6,
        },

        "CASE 4 – Ô nhiễm nặng (kim loại)": {
            'ph': 7.2, 'do_man': 12, 'luong_mua': 2200,
            'nh3': 0.4, 'h2s': 0.02, 'nhiet_do_nuoc_bien': 26,
            'bod5': 20, 'as': 15, 'cd': 1.0,
        },

        "CASE 5 – Rất nguy hiểm (đa chỉ tiêu)": {
            'ph': 5.8, 'do_man': 28, 'luong_mua': 3500,
            'nh3': 1.2, 'h2s': 0.08, 'nhiet_do_nuoc_bien': 32,
            'bod5': 45, 'as': 25, 'cd': 2.5,
        },

        "CASE 6 – Chỉ NH3 vượt nhẹ": {
            'ph': 7.4, 'do_man': 11, 'luong_mua': 2100,
            'nh3': 0.35, 'h2s': 0.006, 'nhiet_do_nuoc_bien': 25,
            'bod5': 6, 'as': 2, 'cd': 0.1,
        },

        "CASE 7 – Chỉ As vượt nặng": {
            'ph': 7.3, 'do_man': 12, 'luong_mua': 2200,
            'nh3': 0.05, 'h2s': 0.004, 'nhiet_do_nuoc_bien': 25,
            'bod5': 5, 'as': 20, 'cd': 0.1,
        },

        "CASE 8 – Ô nhiễm hữu cơ (BOD5)": {
            'ph': 7.0, 'do_man': 14, 'luong_mua': 2300,
            'nh3': 0.3, 'h2s': 0.02, 'nhiet_do_nuoc_bien': 27,
            'bod5': 40, 'as': 4, 'cd': 0.2,
        },

        "CASE 9 – Khí độc H2S": {
            'ph': 7.1, 'do_man': 13, 'luong_mua': 2400,
            'nh3': 0.2, 'h2s': 0.09, 'nhiet_do_nuoc_bien': 26,
            'bod5': 10, 'as': 3, 'cd': 0.2,
        },

        "CASE 10 – Biến đổi khí hậu": {
            'ph': 7.6, 'do_man': 30, 'luong_mua': 3800,
            'nh3': 0.15, 'h2s': 0.01, 'nhiet_do_nuoc_bien': 33,
            'bod5': 8, 'as': 3, 'cd': 0.15,
        },

        "CASE 11 – Kim loại nhẹ đồng thời": {
            'ph': 7.0, 'do_man': 15, 'luong_mua': 2500,
            'nh3': 0.2, 'h2s': 0.015, 'nhiet_do_nuoc_bien': 27,
            'bod5': 10, 'as': 7, 'cd': 0.7,
        },

        "CASE 12 – Nhiều chỉ tiêu vừa vượt": {
            'ph': 6.2, 'do_man': 24, 'luong_mua': 3100,
            'nh3': 0.6, 'h2s': 0.04, 'nhiet_do_nuoc_bien': 31,
            'bod5': 30, 'as': 9, 'cd': 0.8,
        },

        "CASE 13 – Cận ngưỡng nguy hiểm": {
            'ph': 6.0, 'do_man': 20, 'luong_mua': 3000,
            'nh3': 0.49, 'h2s': 0.049, 'nhiet_do_nuoc_bien': 30,
            'bod5': 19, 'as': 9.5, 'cd': 0.95,
        },

        "CASE 14 – Thảm họa sinh thái": {
            'ph': 5.5, 'do_man': 35, 'luong_mua': 4200,
            'nh3': 2.0, 'h2s': 0.15, 'nhiet_do_nuoc_bien': 35,
            'bod5': 60, 'as': 40, 'cd': 4.0,
        },
    }

    for case_name, sample_data in test_cases.items():
        print("\n" + "=" * 90)
        print(case_name)
        print("-" * 90)

        result = calculate_eai(sample_data)

        print(f"EAI = {result['EAI']:.3f} → {result['eai_level']} ({result['eai_color']})")
        print(f"Ghi chú: {result.get('note')}")

        print(f"\nSI_max   = {result['si_max']:.3f}")
        print(f"SI_w_avg = {result['si_w_avg']:.3f}")

        print("\nChi tiết từng thông số:")
        for param, info in result['sub_assessment'].items():
            print(
                f"  {param:<22}: {info['value']:<6} "
                f"→ SI = {info['si']:<5.2f} "
                f"→ {info['level']}"
            )

