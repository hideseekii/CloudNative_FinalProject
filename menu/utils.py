from datetime import datetime, timedelta

def get_pickup_times():
    now = datetime.now().replace(second=0, microsecond=0)
    first_slot = (now + timedelta(minutes=15)).replace(minute=(now.minute // 15 + 1) * 15 % 60)
    pickup_times = ['立即取餐']
    slot_time = first_slot

    for _ in range(32):  # 每15分鐘一個時段，共8小時
        pickup_times.append(slot_time.strftime('%H:%M'))
        slot_time += timedelta(minutes=15)

    return pickup_times
