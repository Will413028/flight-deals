"""Destinations searched from TPE. Edit freely; codes are IATA airports.

Comma-separated codes are searched together (one city, several airports).
`days` is the round-trip length used for the date search.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Destination:
    code: str
    name: str
    region: str
    days: int


def _d(region: str, days: int, *items: tuple[str, str]) -> list[Destination]:
    return [Destination(code, name, region, days) for code, name in items]


DESTINATIONS: list[Destination] = [
    *_d("日本", 5,
        ("NRT,HND", "東京"), ("KIX", "大阪"), ("NGO", "名古屋"), ("FUK", "福岡"),
        ("CTS", "札幌"), ("OKA", "沖繩"), ("SDJ", "仙台"), ("KMJ", "熊本"),
        ("HIJ", "廣島"), ("OKJ", "岡山"), ("TAK", "高松"), ("KOJ", "鹿兒島")),
    *_d("韓國", 5, ("ICN", "首爾"), ("PUS", "釜山"), ("CJU", "濟州")),
    *_d("港澳中國", 4,
        ("HKG", "香港"), ("MFM", "澳門"), ("PVG,SHA", "上海"), ("PEK,PKX", "北京"),
        ("CAN", "廣州"), ("XMN", "廈門"), ("CTU,TFU", "成都")),
    *_d("東南亞", 5,
        ("BKK,DMK", "曼谷"), ("CNX", "清邁"), ("HKT", "普吉島"), ("SGN", "胡志明市"),
        ("HAN", "河內"), ("DAD", "峴港"), ("CXR", "芽莊"), ("MNL", "馬尼拉"),
        ("CEB", "宿霧"), ("SIN", "新加坡"), ("KUL", "吉隆坡"), ("PEN", "檳城"),
        ("CGK", "雅加達"), ("DPS", "峇里島"), ("KTI", "金邊")),
    *_d("南亞中東", 7, ("DEL", "德里"), ("DXB", "杜拜"), ("IST", "伊斯坦堡")),
    *_d("歐洲", 10,
        ("LHR,LGW", "倫敦"), ("CDG", "巴黎"), ("AMS", "阿姆斯特丹"), ("FRA", "法蘭克福"),
        ("MUC", "慕尼黑"), ("VIE", "維也納"), ("PRG", "布拉格"), ("FCO", "羅馬"),
        ("MXP", "米蘭"), ("BCN", "巴塞隆納"), ("MAD", "馬德里"), ("ZRH", "蘇黎世"),
        ("CPH", "哥本哈根"), ("HEL", "赫爾辛基")),
    *_d("大洋洲", 8,
        ("SYD", "雪梨"), ("MEL", "墨爾本"), ("BNE", "布里斯本"), ("PER", "伯斯"),
        ("AKL", "奧克蘭")),
    *_d("關島帛琉", 5, ("GUM", "關島"), ("ROR", "帛琉")),
    *_d("北美", 10,
        ("LAX", "洛杉磯"), ("SFO", "舊金山"), ("SEA", "西雅圖"), ("JFK,EWR", "紐約"),
        ("ORD", "芝加哥"), ("IAH", "休士頓"), ("ONT", "安大略"), ("YVR", "溫哥華"),
        ("YYZ", "多倫多"), ("HNL", "檀香山")),
]
