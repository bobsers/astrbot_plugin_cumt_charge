import asyncio
import json
import re
from datetime import datetime
from typing import Any

import astrbot.api.message_components as Comp
import httpx

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star

DETAIL_URL = "https://api.powerliber.com/client/1/device/detail"
PROFILE_URL = "https://power-api.powerliber.com/client/2/device/profile"
TOKEN = "your_token_here"
CLIENT_ID = "1"
APP_ID = "dd"
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 26_1 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 "
        "MicroMessenger/8.0.71(0x18004730) NetType/4G Language/zh_CN"
    ),
    "Referer": "https://servicewechat.com/wx5835f6c1219c749f/427/page-frame.html",
}
MONITOR_STATE_KEY = "monitor_state"
MONITOR_INTERVAL_SECONDS = 300
FORWARD_NODE_MAX_CHARS = 900
FORWARD_BATCH_MAX_NODES = 6
FORWARD_BATCH_MAX_CHARS = 3600

FIELD_LABELS = {
    "code": "返回码",
    "data": "数据",
    "device": "设备信息",
    "devicedetail": "实时设备信息",
    "station": "站点信息",
    "stationid": "站点 ID",
    "stationname": "站点名称",
    "stationcount": "站点数量",
    "orgdetail": "组织信息",
    "orgid": "组织 ID",
    "orgname": "组织名称",
    "orgphone": "组织电话",
    "orgaddress": "组织地址",
    "operatorconfig": "运营配置",
    "chargeconfig": "充电配置",
    "chargemodel": "计费模型",
    "name": "名称",
    "id": "ID",
    "uid": "设备 UID",
    "suid": "扫码短码",
    "uuid": "UUID",
    "type": "类型",
    "mode": "模式",
    "status": "状态",
    "address": "地址",
    "province": "省",
    "city": "市",
    "county": "区县",
    "street": "街道",
    "longitude": "经度",
    "latitude": "纬度",
    "phone": "联系电话",
    "operatorid": "运营商 ID",
    "operatorname": "运营商名称",
    "operatorphone": "运营商电话",
    "username": "用户名称",
    "userid": "用户 ID",
    "deviceid": "设备 ID",
    "devicecount": "设备数量",
    "devicetype": "设备类型",
    "portcount": "端口数量",
    "portindex": "端口号",
    "portlist": "端口列表",
    "nodeindex": "节点索引",
    "pluggatewayuid": "插座网关 UID",
    "gatewayid": "网关 ID",
    "gatewaychannel": "网关通道",
    "space": "点位编号",
    "rssi": "信号强度 RSSI",
    "sp": "SP 参数",
    "online": "在线状态",
    "onlinestatus": "在线状态",
    "current": "电流",
    "voltage": "电压",
    "power": "功率",
    "totalchargepower": "总充电功率",
    "energyconsumed": "已耗电量",
    "timeconsumed": "已充时长",
    "transactionid": "交易流水号",
    "batteryid": "电池 ID",
    "packid": "电池包 ID",
    "mark": "标记",
    "relaytemperature": "继电器温度",
    "communicationstatus": "通信状态",
    "doorstatus": "柜门状态",
    "cabinetstatus": "柜体状态",
    "occupystatus": "占位状态",
    "plugin": "插枪状态",
    "fanstatus": "风扇状态",
    "heaterstatus": "加热器状态",
    "flaghasbattery": "检测到电池",
    "flagnoload": "空载标记",
    "flagovercurrent": "过流告警",
    "flagoverload": "过载告警",
    "flagovertemperature": "过温告警",
    "flagsmokealarm": "烟雾告警",
    "flagwaterimmersion": "水浸告警",
    "flagerror": "故障标记",
    "emergencybuttonstate": "急停按钮状态",
    "chargestatus": "充电状态",
    "powerdirectchargeconfigid": "直充配置 ID",
    "resourcepackageconfigid": "资源包配置 ID",
    "resourcepackageconfigname": "资源包配置名称",
    "chargeconfigid": "充电配置 ID",
    "chargeconfigname": "充电配置名称",
    "chargefullenable": "充满自停开关",
    "chargefullmoney": "充满自停金额",
    "chargefullmoneymin": "充满自停最小金额",
    "chargefullpremoney": "充满预付金额",
    "chargecabinetchargefullenable": "柜机充满自停开关",
    "chargecabinetchargefullmoney": "柜机充满自停金额",
    "chargecabinetchargefullmoneymin": "柜机充满自停最小金额",
    "chargepreoccupyfeeconfig": "充电前占位费配置",
    "chargefinishoccupyfeeconfig": "充电结束占位费配置",
    "custommoney": "自定义金额选项",
    "deposit": "押金",
    "exchangemode": "换电模式",
    "freetime": "免费时长",
    "freechargetime": "免费充电时长",
    "freelowenergythreshold": "低电量免费阈值",
    "servicefeemoney": "服务费金额",
    "servicefeemode": "服务费模式",
    "servicefeefreetime": "服务费免费时长",
    "servicefeelist": "服务费列表",
    "occupylist": "占位规则列表",
    "occupyfreeminute": "占位免费分钟数",
    "occupypreprice": "占位预收费",
    "takebatterycount": "取电池数量",
    "unitname": "计费单位名称",
    "minmoney": "最小金额",
    "minconsumemoney": "最小消费金额",
    "price": "价格",
    "time": "时长",
    "capacitymin": "容量下限",
    "capacitymax": "容量上限",
    "virtualcardprecharge": "虚拟卡预充金额",
    "ykcchargeconfig": "月卡充电配置",
    "reportconfig": "上报配置",
    "reportstrategy": "上报策略",
    "disablechargeconfig": "禁充配置",
    "memberpriceconfig": "会员价配置",
    "voiceconfig": "语音配置",
    "energychargeenable": "电量计费开关",
    "energyprice": "电价",
    "energyratio": "电量系数",
    "energychargeclearingconfigid": "电量计费结算配置 ID",
    "energychargeclearingconfigname": "电量计费结算配置名称",
    "autorefundvirtualcard": "虚拟卡自动退款",
    "autorefundqrcode": "二维码自动退款",
    "autorefundminmoneyvirtualcard": "虚拟卡自动退款最低金额",
    "autorefundminmoneyqrcode": "二维码自动退款最低金额",
    "autorefundminmoneycard": "实体卡自动退款最低金额",
    "cardchargeenable": "实体卡充电开关",
    "packagecardchargeenable": "套餐卡充电开关",
    "virtualcardchargeenable": "虚拟卡充电开关",
    "virtualpackagecardchargeenable": "虚拟套餐卡充电开关",
    "virtualcardenable": "虚拟卡开关",
    "virtualpackagecardenable": "虚拟套餐卡开关",
    "cardmode": "实体卡模式",
    "carddeductionmode": "实体卡扣费模式",
    "wxenable": "微信支付开关",
    "wxpayscoreenable": "微信分付开关",
    "wxservicefollowmode": "微信服务关注模式",
    "alipayenable": "支付宝开关",
    "qrcodeenable": "二维码支付开关",
    "rechargeenable": "充值开关",
    "rechargeconfigid": "充值配置 ID",
    "rechargeconfigname": "充值配置名称",
    "rechargeconfigmode": "充值配置模式",
    "rechargeconfigstarttime": "充值配置开始时间",
    "rechargeconfigfinishtime": "充值配置结束时间",
    "rechargeclearingconfigid": "充值结算配置 ID",
    "rechargeclearingconfigname": "充值结算配置名称",
    "rechargecarconfigid": "车辆充值配置 ID",
    "rechargecarconfigname": "车辆充值配置名称",
    "rechargecarconfigmode": "车辆充值配置模式",
    "rechargecarconfigstarttime": "车辆充值配置开始时间",
    "rechargecarconfigfinishtime": "车辆充值配置结束时间",
    "prechargeconfigid": "预约充电配置 ID",
    "prechargereservetime": "预约保留时长",
    "caroccupychargeconfigid": "车位占用收费配置 ID",
    "targetid": "目标 ID",
    "targettype": "目标类型",
    "paychannel": "支付渠道",
    "paymessage": "支付提示",
    "paymethodlist": "支付方式列表",
    "flagcardglobalavailable": "全局卡可用标记",
    "flagindependentcharge": "独立充电标记",
    "flagindependentpay": "独立支付标记",
    "flaginsurance": "保险标记",
    "flagwxindependent": "微信独立支付标记",
    "flagwxpay": "微信支付标记",
    "flagalipay": "支付宝标记",
    "flagpaymessage": "支付提示开关",
    "flagbfpay": "BF 支付标记",
    "flagbfpostpay": "BF 后付费标记",
    "flagrealidverify": "实名认证标记",
    "flagad": "广告开关",
    "flagadafterpay": "支付后广告开关",
    "flaginvoice": "发票开关",
    "flagmemberprice": "会员价开关",
    "flagvoice": "语音开关",
    "flagdisablecharge": "禁充开关",
    "flagprecharge": "预约充电开关",
    "flagprechargecharge": "预约后自动充电开关",
    "flagcaroccupyaftercharge": "充电后车位占用收费开关",
    "flagcaroccupybeforecharge": "充电前车位占用收费开关",
    "flagenergychargeclearing": "电量计费结算开关",
    "flagshowchargedetail": "展示充电明细",
    "flagdisplaychargedetail": "显示充电明细",
    "flagchargefullpremoney": "充满预付金额开关",
    "flaggateenable": "闸机联动开关",
    "flagmoneyconsumecalplatform": "平台金额计费开关",
    "flagminconsumemoney": "最小消费金额开关",
    "flagfreelowenergy": "低电量免费开关",
    "flagcustomfreechargetime": "自定义免费充电时长开关",
    "flagcardmultipleorder": "实体卡多订单开关",
    "flagpackagecardmultipleorder": "套餐卡多订单开关",
    "flagvirtualcardmultipleorder": "虚拟卡多订单开关",
    "flaguserapplyrefund": "用户自主退款开关",
    "flagvincharge": "VIN 充电开关",
    "flagmoneyfactor6x": "6 倍金额系数标记",
    "flagautoclose": "自动关闭标记",
    "flagindependentconfig": "独立配置标记",
    "iscloseorderindisablecharge": "禁充时关闭订单",
    "isdefault": "是否默认",
    "list": "列表",
    "mostexpensivepricebyenergy": "按电量最贵单价",
    "mostexpensivepricebytime": "按时长最贵单价",
    "appid": "应用 ID",
    "bfsubmerchantno": "BF 子商户号",
    "p1status": "1 号口状态",
    "p1transactionid": "1 号口交易流水号",
    "p2status": "2 号口状态",
    "p2transactionid": "2 号口交易流水号",
    "lastactivetime": "最后活跃时间",
    "createtime": "创建时间",
    "updatetime": "更新时间",
    "todayincome": "今日收入",
    "usage": "使用率",
    "statarpu": "统计 ARPU",
    "arpu": "ARPU",
    "statusagerate": "统计使用率",
    "usecount": "使用次数",
    "workerid": "工作人员 ID",
    "regioncode": "区域编码",
    "tenement": "物业名称",
    "tenementcontacts": "物业联系人",
    "tenementcontactsphone": "物业联系人电话",
    "remark": "备注",
    "chargeconfigid": "充电配置 ID",
}

TOKEN_LABELS = {
    "ad": "广告",
    "address": "地址",
    "alipay": "支付宝",
    "app": "应用",
    "arpu": "ARPU",
    "auto": "自动",
    "available": "可用",
    "battery": "电池",
    "bf": "BF",
    "button": "按钮",
    "cabinet": "柜机",
    "cal": "计算",
    "capacity": "容量",
    "card": "卡",
    "car": "车辆",
    "channel": "通道",
    "charge": "充电",
    "charging": "充电",
    "city": "市",
    "clearing": "结算",
    "close": "关闭",
    "code": "编码",
    "communication": "通信",
    "config": "配置",
    "contacts": "联系人",
    "consume": "消费",
    "consumed": "已耗",
    "count": "数量",
    "county": "区县",
    "create": "创建",
    "current": "电流",
    "custom": "自定义",
    "data": "数据",
    "deduction": "扣费",
    "default": "默认",
    "deposit": "押金",
    "detail": "详情",
    "device": "设备",
    "disable": "禁用",
    "display": "显示",
    "door": "柜门",
    "emergency": "急停",
    "enable": "开关",
    "energy": "电量",
    "error": "故障",
    "exchange": "换电",
    "expensive": "最贵",
    "fan": "风扇",
    "fee": "费",
    "finish": "结束",
    "flag": "标记",
    "follow": "关注",
    "free": "免费",
    "full": "充满",
    "gate": "闸机",
    "gateway": "网关",
    "global": "全局",
    "group": "群组",
    "has": "有",
    "heater": "加热器",
    "id": "ID",
    "immersion": "浸水",
    "income": "收入",
    "independent": "独立",
    "insurance": "保险",
    "invoice": "发票",
    "last": "最后",
    "latitude": "纬度",
    "list": "列表",
    "load": "过载",
    "longitude": "经度",
    "mark": "标记",
    "max": "最大",
    "member": "会员",
    "merchant": "商户",
    "min": "最小",
    "mode": "模式",
    "model": "模型",
    "money": "金额",
    "most": "最",
    "name": "名称",
    "no": "无",
    "node": "节点",
    "occupy": "占位",
    "online": "在线",
    "operator": "运营商",
    "order": "订单",
    "org": "组织",
    "over": "过",
    "pack": "包",
    "package": "套餐",
    "pay": "支付",
    "phone": "电话",
    "platform": "平台",
    "plug": "插枪",
    "port": "端口",
    "post": "后",
    "power": "功率",
    "pre": "预",
    "price": "价格",
    "profile": "状态",
    "protocol": "协议",
    "province": "省",
    "qrcode": "二维码",
    "ratio": "系数",
    "real": "真实",
    "recharge": "充值",
    "refund": "退款",
    "region": "区域",
    "relay": "继电器",
    "report": "上报",
    "reserve": "保留",
    "resource": "资源",
    "rssi": "RSSI",
    "score": "分值",
    "service": "服务",
    "show": "展示",
    "smoke": "烟雾",
    "space": "点位",
    "start": "开始",
    "stat": "统计",
    "station": "站点",
    "status": "状态",
    "street": "街道",
    "sub": "子",
    "suid": "扫码短码",
    "target": "目标",
    "temperature": "温度",
    "tenement": "物业",
    "time": "时间",
    "today": "今日",
    "total": "总",
    "transaction": "交易",
    "type": "类型",
    "uid": "UID",
    "unit": "单位",
    "update": "更新",
    "usage": "使用率",
    "use": "使用",
    "user": "用户",
    "vin": "VIN",
    "virtual": "虚拟",
    "voice": "语音",
    "voltage": "电压",
    "water": "水浸",
    "weight": "权重",
    "worker": "工作人员",
    "wx": "微信",
    "ykc": "月卡",
}

TIMESTAMP_KEYS = {
    "createtime",
    "updatetime",
    "lastactivetime",
    "rechargeconfigstarttime",
    "rechargeconfigfinishtime",
    "rechargecarconfigstarttime",
    "rechargecarconfigfinishtime",
}

ALARM_KEYS = {
    "flagovercurrent",
    "flagoverload",
    "flagovertemperature",
    "flagsmokealarm",
    "flagwaterimmersion",
    "flagerror",
}

SWITCH_KEYS = {
    "wxenable",
    "wxpayscoreenable",
    "alipayenable",
    "qrcodeenable",
    "rechargeenable",
    "cardchargeenable",
    "packagecardchargeenable",
    "virtualcardchargeenable",
    "virtualpackagecardchargeenable",
    "virtualcardenable",
    "virtualpackagecardenable",
    "chargefullenable",
    "chargecabinetchargefullenable",
    "energychargeenable",
    "flagpaymessage",
    "flagad",
    "flagadafterpay",
    "flaginvoice",
    "flagmemberprice",
    "flagvoice",
    "flagdisablecharge",
    "flagprecharge",
    "flagprechargecharge",
    "flagcaroccupyaftercharge",
    "flagcaroccupybeforecharge",
    "flagenergychargeclearing",
    "flagshowchargedetail",
    "flagdisplaychargedetail",
    "flagchargefullpremoney",
    "flaggateenable",
    "flagminconsumemoney",
    "flagfreelowenergy",
    "flagcustomfreechargetime",
    "flagcardmultipleorder",
    "flagpackagecardmultipleorder",
    "flagvirtualcardmultipleorder",
    "flaguserapplyrefund",
    "flagvincharge",
}

STATUS_VALUE_MAPS = {
    "online": {0: "离线", 1: "在线"},
    "onlinestatus": {0: "离线", 1: "在线"},
    "chargestatus": {0: "空闲", 1: "充电中"},
    "plugin": {0: "未插入", 1: "已插入"},
    "doorstatus": {0: "关闭", 1: "打开"},
    "emergencybuttonstate": {0: "正常", 1: "已按下"},
    "fanstatus": {0: "关闭", 1: "开启"},
    "heaterstatus": {0: "关闭", 1: "开启"},
    "flaghasbattery": {0: "否", 1: "是"},
    "flagrealidverify": {0: "未要求", 1: "已要求"},
    "flagindependentcharge": {0: "否", 1: "是"},
    "flagindependentpay": {0: "否", 1: "是"},
    "flagcardglobalavailable": {0: "否", 1: "是"},
    "flaginsurance": {0: "否", 1: "是"},
    "flagwxindependent": {0: "否", 1: "是"},
    "flagwxpay": {0: "否", 1: "是"},
    "flagalipay": {0: "否", 1: "是"},
}

JSON_STRING_KEYS = {
    "data",
    "list",
    "port_list",
    "occupy_list",
    "occupyList",
    "memberPriceConfig",
    "member_price_config",
}


def _default_state() -> dict[str, Any]:
    return {
        "monitor_enabled": False,
        "monitor_suids": [],
        "monitor_target_umo": "",
        "monitor_self_id": "0",
        "station_cache": {},
    }


def _merge_state(data: Any) -> dict[str, Any]:
    state = _default_state()
    if not isinstance(data, dict):
        return state

    state["monitor_enabled"] = bool(data.get("monitor_enabled", False))
    state["monitor_target_umo"] = str(data.get("monitor_target_umo", "") or "")
    state["monitor_self_id"] = str(data.get("monitor_self_id", "0") or "0")

    suids = data.get("monitor_suids", [])
    if isinstance(suids, list):
        state["monitor_suids"] = _unique_suids(
            [str(item).strip() for item in suids if str(item).strip()]
        )

    station_cache = data.get("station_cache", {})
    if isinstance(station_cache, dict):
        state["station_cache"] = {
            str(key).strip(): str(value).strip()
            for key, value in station_cache.items()
            if str(key).strip()
        }
    return state


def _unique_suids(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def _extract_command_tail(message_str: str, command_name: str) -> str:
    text = (message_str or "").strip()
    pattern = rf"^/?{re.escape(command_name)}(?:\s+|$)"
    return re.sub(pattern, "", text, count=1).strip()


def _looks_like_suid(text: str) -> bool:
    return bool(re.fullmatch(r"\d{8,}", text.strip()))


def _join_port_labels(ports: list[dict[str, Any]]) -> str:
    return "、".join(_port_label(port) for port in ports)


def _find_port_by_number(
    ports: list[dict[str, Any]], port_number: int
) -> dict[str, Any] | None:
    for port in ports:
        if _safe_int(port.get("port_index")) + 1 == port_number:
            return port
    return None


class PowerLiberApiError(RuntimeError):
    pass


class PowerLiberClient:
    def __init__(self) -> None:
        self._client = httpx.AsyncClient(
            headers=DEFAULT_HEADERS,
            timeout=httpx.Timeout(10.0, connect=5.0),
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def device_detail(self, suid: str) -> dict[str, Any]:
        return await self._post(
            DETAIL_URL,
            {
                "token": TOKEN,
                "client_id": CLIENT_ID,
                "app_id": APP_ID,
                "suid": suid,
            },
        )

    async def device_profile(self, uid: str) -> dict[str, Any]:
        return await self._post(
            PROFILE_URL,
            {
                "token": TOKEN,
                "client_id": CLIENT_ID,
                "app_id": APP_ID,
                "uid": uid,
            },
        )

    async def _post(self, url: str, payload: dict[str, str]) -> dict[str, Any]:
        try:
            response = await self._client.post(url, data=payload)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPStatusError as exc:
            raise PowerLiberApiError(f"HTTP {exc.response.status_code}") from exc
        except httpx.HTTPError as exc:
            raise PowerLiberApiError(f"网络请求失败: {exc}") from exc
        except json.JSONDecodeError as exc:
            raise PowerLiberApiError("接口返回的不是合法 JSON") from exc

        if data.get("code") != 0:
            message = data.get("msg") or data.get("message") or "未知错误"
            raise PowerLiberApiError(f"code={data.get('code')} message={message}")
        return data


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _normalize_key(key: str) -> str:
    snake = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", key)
    return snake.replace("_", "").lower()


def _split_key_tokens(key: str) -> list[str]:
    snake = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", key).lower()
    return [token for token in snake.split("_") if token]


def _label_for_key(key: str) -> str:
    normalized = _normalize_key(key)
    if normalized in FIELD_LABELS:
        return FIELD_LABELS[normalized]

    tokens = _split_key_tokens(key)
    if not tokens:
        return key

    translated = []
    for token in tokens:
        translated.append(
            TOKEN_LABELS.get(token, token.upper() if len(token) <= 3 else token)
        )
    return "".join(translated)


def _station_name(detail_json: dict[str, Any]) -> str:
    return (
        detail_json.get("data", {}).get("device", {}).get("station_name") or "未知站点"
    )


def _device_uid(detail_json: dict[str, Any]) -> str:
    uid = detail_json.get("data", {}).get("device", {}).get("uid")
    if not uid:
        raise PowerLiberApiError("detail 接口未返回 uid")
    return str(uid)


def _port_label(port: dict[str, Any]) -> str:
    return f"{_safe_int(port.get('port_index')) + 1}号口"


def _is_healthy(port: dict[str, Any]) -> bool:
    fault_keys = (
        "flag_over_load",
        "flag_over_current",
        "flag_over_temperature",
        "flag_smoke_alarm",
        "flag_water_immersion",
        "emergency_button_state",
    )
    return all(_safe_int(port.get(key)) == 0 for key in fault_keys)


def _is_available(port: dict[str, Any]) -> bool:
    return (
        _safe_int(port.get("online")) == 1
        and _safe_int(port.get("charge_status")) == 0
        and _is_healthy(port)
    )


def _is_idle_like(port: dict[str, Any]) -> bool:
    return (
        _safe_int(port.get("online")) == 1
        and _is_healthy(port)
        and _safe_float(port.get("power")) <= 1.0
        and _safe_int(port.get("current")) <= 10
        and _safe_int(port.get("time_consumed")) == 0
        and _safe_int(port.get("energy_consumed")) == 0
    )


def _select_available_ports(
    profile_json: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    ports = profile_json.get("data", {}).get("port_list", [])
    if not isinstance(ports, list):
        raise PowerLiberApiError("profile 接口未返回有效的 port_list")

    strict_ports = sorted(
        (port for port in ports if isinstance(port, dict) and _is_available(port)),
        key=lambda item: _safe_int(item.get("port_index")),
    )
    idle_ports = sorted(
        (
            port
            for port in ports
            if isinstance(port, dict)
            and _is_idle_like(port)
            and port not in strict_ports
        ),
        key=lambda item: _safe_int(item.get("port_index")),
    )
    return strict_ports, idle_ports


def _format_timestamp(value: int) -> str:
    if value <= 0:
        return str(value)
    if value > 10**12:
        value = value // 1000
    return datetime.fromtimestamp(value).strftime("%Y-%m-%d %H:%M:%S")


def _maybe_parse_json_string(key: str, value: Any) -> Any:
    if not isinstance(value, str):
        return value

    text = value.strip()
    if not text:
        return value
    if key not in JSON_STRING_KEYS and text[0] not in "[{":
        return value

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return value


def _format_scalar(key: str, value: Any) -> str:
    normalized = _normalize_key(key)

    if value is None:
        return "null"
    if value == "":
        return "空"
    if isinstance(value, bool):
        return "是" if value else "否"

    if normalized in TIMESTAMP_KEYS and isinstance(value, (int, float)):
        return _format_timestamp(int(value))

    if normalized in STATUS_VALUE_MAPS:
        mapped = STATUS_VALUE_MAPS[normalized].get(_safe_int(value))
        if mapped is not None:
            return f"{mapped} ({value})"

    if normalized in ALARM_KEYS:
        return f"{'告警' if _safe_int(value) else '正常'} ({value})"

    if normalized in SWITCH_KEYS or normalized.endswith("enable"):
        return f"{'开启' if _safe_int(value) else '关闭'} ({value})"

    if normalized.startswith("flag"):
        return f"{'是' if _safe_int(value) else '否'} ({value})"

    if normalized == "current":
        current = _safe_int(value)
        return f"{current} mA ({current / 1000:.3f} A)"
    if normalized == "voltage":
        voltage = _safe_int(value)
        return f"{voltage} ({voltage / 100:.1f} V)"
    if normalized in {"power", "totalchargepower"}:
        return f"{_safe_float(value):.1f} W"
    if normalized == "portindex":
        port_index = _safe_int(value)
        return f"{port_index + 1}号口 (索引 {port_index})"
    if normalized == "energyconsumed":
        return f"{value} (原始电量值)"
    if normalized == "timeconsumed":
        return f"{value} 分钟"
    if isinstance(value, float):
        return f"{value:.6f}".rstrip("0").rstrip(".")
    if isinstance(value, list):
        return ", ".join(str(item) for item in value)
    return str(value)


def _render_lines(
    data: Any,
    *,
    indent: int = 0,
    omit_keys: set[str] | None = None,
) -> list[str]:
    omit_keys = omit_keys or set()
    prefix = "  " * indent
    lines: list[str] = []

    if isinstance(data, dict):
        for key, raw_value in data.items():
            if key in omit_keys:
                if key == "port_list":
                    lines.append(f"{prefix}{_label_for_key(key)}：已拆分到独立端口节点")
                continue

            value = _maybe_parse_json_string(key, raw_value)
            label = _label_for_key(key)

            if isinstance(value, dict):
                lines.append(f"{prefix}{label}：")
                lines.extend(_render_lines(value, indent=indent + 1))
                continue

            if isinstance(value, list):
                if key == "port_list":
                    lines.append(f"{prefix}{label}：已拆分到独立端口节点")
                    continue

                if not value:
                    lines.append(f"{prefix}{label}：[]")
                    continue

                lines.append(f"{prefix}{label}：")
                if all(not isinstance(item, (dict, list)) for item in value):
                    for item in value:
                        lines.append(f"{prefix}  - {_format_scalar(key, item)}")
                else:
                    for index, item in enumerate(value, start=1):
                        lines.append(f"{prefix}  第 {index} 项：")
                        lines.extend(_render_lines(item, indent=indent + 2))
                continue

            lines.append(f"{prefix}{label}：{_format_scalar(key, value)}")
        return lines

    if isinstance(data, list):
        for index, item in enumerate(data, start=1):
            lines.append(f"{prefix}第 {index} 项：")
            lines.extend(_render_lines(item, indent=indent + 1))
        return lines

    lines.append(f"{prefix}{data}")
    return lines


def _render_section(
    title: str,
    data: Any,
    *,
    omit_keys: set[str] | None = None,
    notes: list[str] | None = None,
) -> str:
    lines = [title]
    if notes:
        lines.extend(notes)
    lines.extend(_render_lines(data, omit_keys=omit_keys))
    return "\n".join(lines)


def _build_charge_full_messages(
    detail_json: dict[str, Any],
    profile_json: dict[str, Any],
) -> list[str]:
    detail_device = detail_json.get("data", {}).get("device", {})
    profile_data = profile_json.get("data", {})
    profile_device = profile_data.get("device_detail", {})
    org_detail = profile_data.get("org_detail", {})
    charge_model = profile_data.get("charge_model", {})
    ports = profile_data.get("port_list", [])

    station = detail_device.get("station", {})
    station_charge_config = (
        station.get("charge_config", {}) if isinstance(station, dict) else {}
    )
    station_basic = dict(station) if isinstance(station, dict) else {}
    station_basic.pop("charge_config", None)

    operator_config = detail_device.get("operator_config", {})

    org_basic = dict(org_detail) if isinstance(org_detail, dict) else {}
    org_operator_config = org_basic.pop("operator_config", {})

    strict_ports, idle_ports = _select_available_ports(profile_json)
    summary_lines = [
        "查询总览",
        f"查询时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"站点名称：{_station_name(detail_json)}",
        f"扫码短码：{detail_device.get('suid', '未知')}",
        f"设备 UID：{detail_device.get('uid', '未知')}",
        f"端口总数：{len(ports)}",
        "严格空闲口："
        + (
            "、".join(_port_label(port) for port in strict_ports)
            if strict_ports
            else "无"
        ),
        "疑似空闲口："
        + ("、".join(_port_label(port) for port in idle_ports) if idle_ports else "无"),
        "说明：以下内容已按字段翻译并拆分；端口信息为每个充电口单独一条。",
    ]

    detail_device_basic = dict(detail_device) if isinstance(detail_device, dict) else {}
    detail_device_basic.pop("station", None)
    detail_device_basic.pop("operator_config", None)
    detail_device_basic.pop("port_list", None)

    profile_device_basic = (
        dict(profile_device) if isinstance(profile_device, dict) else {}
    )
    profile_device_basic.pop("station", None)
    profile_device_basic.pop("operator_config", None)
    profile_device_basic.pop("port_list", None)

    messages = ["\n".join(summary_lines)]
    messages.append(
        _render_section(
            "扫码详情接口 /data/device",
            detail_device_basic,
            notes=["端口列表、站点信息、运营配置已拆到后续节点。"],
        )
    )
    if station_basic:
        messages.append(_render_section("站点信息 /data/device/station", station_basic))
    if station_charge_config:
        messages.append(
            _render_section(
                "站点充电配置 /data/device/station/charge_config",
                station_charge_config,
            )
        )
    if operator_config:
        messages.append(
            _render_section("运营配置 /data/device/operator_config", operator_config)
        )
    if profile_device_basic:
        messages.append(
            _render_section(
                "实时状态接口 /data/device_detail",
                profile_device_basic,
                notes=["端口列表、站点信息、运营配置已拆到其他节点或前文节点。"],
            )
        )
    if org_basic:
        messages.append(_render_section("组织信息 /data/org_detail", org_basic))
    if org_operator_config:
        messages.append(
            _render_section(
                "组织运营配置 /data/org_detail/operator_config",
                org_operator_config,
            )
        )
    if charge_model:
        messages.append(_render_section("计费模型 /data/charge_model", charge_model))

    for port in ports:
        if isinstance(port, dict):
            messages.append(_render_section(f"端口详情 {_port_label(port)}", port))

    return messages


def _split_forward_text(
    message: str, max_chars: int = FORWARD_NODE_MAX_CHARS
) -> list[str]:
    if len(message) <= max_chars:
        return [message]

    lines = message.splitlines()
    if not lines:
        return [message]

    title = lines[0]
    body_lines = lines[1:]
    chunks: list[str] = []
    current = title
    first_chunk = True

    for line in body_lines:
        candidate = current + "\n" + line
        if len(candidate) <= max_chars:
            current = candidate
            continue

        chunks.append(current)
        prefix = f"{title}（续）" if first_chunk else f"{title}（续{len(chunks)}）"
        current = prefix + "\n" + line
        first_chunk = False

        if len(current) <= max_chars:
            continue

        # Handle a single extra-long line by hard-splitting it.
        header = prefix + "\n"
        available = max_chars - len(header)
        remaining = line
        while len(remaining) > available > 0:
            chunks.append(header + remaining[:available])
            remaining = remaining[available:]
            prefix = f"{title}（续{len(chunks)}）"
            header = prefix + "\n"
            available = max_chars - len(header)
        current = header + remaining if remaining else prefix

    if current:
        chunks.append(current)
    return chunks


def _build_forward_chains(
    event: AstrMessageEvent, messages: list[str]
) -> list[list[Comp.Nodes]]:
    self_id = str(getattr(event.message_obj, "self_id", "") or "0")
    node_name = "CUMTCharge"
    nodes: list[Comp.Node] = []

    for message in messages:
        for part in _split_forward_text(message):
            nodes.append(
                Comp.Node(
                    uin=self_id,
                    name=node_name,
                    content=[Comp.Plain(part)],
                )
            )

    batches: list[list[Comp.Nodes]] = []
    current_nodes: list[Comp.Node] = []
    current_chars = 0

    for node in nodes:
        text_len = sum(
            len(component.text)
            for component in node.content
            if hasattr(component, "text")
        )
        if current_nodes and (
            len(current_nodes) >= FORWARD_BATCH_MAX_NODES
            or current_chars + text_len > FORWARD_BATCH_MAX_CHARS
        ):
            batches.append([Comp.Nodes(nodes=current_nodes)])
            current_nodes = []
            current_chars = 0

        current_nodes.append(node)
        current_chars += text_len

    if current_nodes:
        batches.append([Comp.Nodes(nodes=current_nodes)])

    return batches


class CumtChargePlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self._api = PowerLiberClient()
        self._state_lock = asyncio.Lock()
        self._state_loaded = False
        self._state = _default_state()
        self._monitor_wakeup = asyncio.Event()
        self._monitor_task = asyncio.get_running_loop().create_task(
            self._monitor_loop()
        )

    async def _ensure_state_loaded(self) -> None:
        if self._state_loaded:
            return

        async with self._state_lock:
            if self._state_loaded:
                return
            raw_state = await self.get_kv_data(MONITOR_STATE_KEY, _default_state())
            self._state = _merge_state(raw_state)
            self._state_loaded = True

    async def _persist_state_locked(self) -> None:
        await self.put_kv_data(MONITOR_STATE_KEY, self._state)

    async def _get_state_snapshot(self) -> dict[str, Any]:
        await self._ensure_state_loaded()
        async with self._state_lock:
            return {
                "monitor_enabled": self._state["monitor_enabled"],
                "monitor_suids": list(self._state["monitor_suids"]),
                "monitor_target_umo": self._state["monitor_target_umo"],
                "monitor_self_id": self._state["monitor_self_id"],
                "station_cache": dict(self._state["station_cache"]),
            }

    async def _set_station_cache(self, suid: str, station_name: str) -> None:
        await self._ensure_state_loaded()
        async with self._state_lock:
            if self._state["station_cache"].get(suid) == station_name:
                return
            self._state["station_cache"][suid] = station_name
            await self._persist_state_locked()

    async def _check_target(self, suid: str) -> dict[str, Any]:
        detail_json = await self._api.device_detail(suid)
        station_name = _station_name(detail_json)
        await self._set_station_cache(suid, station_name)
        uid = _device_uid(detail_json)
        profile_json = await self._api.device_profile(uid)
        strict_ports, idle_ports = _select_available_ports(profile_json)
        return {
            "suid": suid,
            "detail_json": detail_json,
            "profile_json": profile_json,
            "station_name": station_name,
            "strict_ports": strict_ports,
            "idle_ports": idle_ports,
        }

    async def _get_station_candidates(self) -> dict[str, str]:
        snapshot = await self._get_state_snapshot()
        candidates = dict(snapshot["station_cache"])
        changed = False

        for suid in snapshot["monitor_suids"]:
            if candidates.get(suid):
                continue
            try:
                detail_json = await self._api.device_detail(suid)
            except PowerLiberApiError:
                logger.exception("刷新站点名称缓存失败: %s", suid)
                continue
            candidates[suid] = _station_name(detail_json)
            changed = True

        if changed:
            async with self._state_lock:
                self._state["station_cache"].update(candidates)
                await self._persist_state_locked()
        return {suid: name for suid, name in candidates.items() if name}

    async def _resolve_query_to_suid(self, query: str) -> tuple[str | None, str | None]:
        query = query.strip()
        if not query:
            return None, "请输入 suid 或站点名称正则。"

        snapshot = await self._get_state_snapshot()
        if (
            query in snapshot["monitor_suids"]
            or query in snapshot["station_cache"]
            or _looks_like_suid(query)
        ):
            return query, None

        candidates = await self._get_station_candidates()
        if not candidates:
            return (
                None,
                "当前没有可用的站点名称映射。先用 /charge add <suid> 加入监听列表。",
            )

        try:
            pattern = re.compile(query)
        except re.error as exc:
            return None, f"站点名称正则无效：{exc}"

        matches = [
            (suid, name) for suid, name in candidates.items() if pattern.search(name)
        ]
        if not matches:
            return None, "未在监听列表的站点名称映射中找到匹配。"
        if len(matches) > 1:
            lines = ["匹配到多个站点，请使用更精确的正则："]
            lines.extend(f"{suid} | {name}" for suid, name in matches)
            return None, "\n".join(lines)
        return matches[0][0], None

    def _format_charge_result(
        self, result: dict[str, Any], include_suid: bool = False
    ) -> str:
        suid = result["suid"]
        station_name = result["station_name"]
        prefix = (
            f"{suid} | {station_name}" if include_suid else f"{station_name} ({suid})"
        )
        strict_ports = result["strict_ports"]
        idle_ports = result["idle_ports"]

        if strict_ports:
            return f"{prefix} 有空余充电口：{_join_port_labels(strict_ports)}"
        if idle_ports:
            return f"{prefix} 接口未返回明确空闲口，但按功率/电流推断疑似空闲：{_join_port_labels(idle_ports)}"
        return f"{prefix} 无空余充电口"

    async def _handle_charge_add(self, suid: str) -> str:
        suid = suid.strip()
        if not suid:
            return "用法：/charge add <suid>"

        try:
            detail_json = await self._api.device_detail(suid)
        except PowerLiberApiError as exc:
            logger.exception("添加监听 suid 失败")
            return f"添加失败：{exc}"

        station_name = _station_name(detail_json)
        await self._ensure_state_loaded()
        async with self._state_lock:
            if suid not in self._state["monitor_suids"]:
                self._state["monitor_suids"].append(suid)
            self._state["station_cache"][suid] = station_name
            await self._persist_state_locked()
        self._monitor_wakeup.set()
        return f"已加入监听：{suid} | {station_name}"

    async def _handle_charge_list(self) -> str:
        snapshot = await self._get_state_snapshot()
        suids = snapshot["monitor_suids"]
        if not suids:
            return "监听列表为空。"

        lines = [
            f"监听状态：{'开启' if snapshot['monitor_enabled'] else '关闭'}",
            "监听列表：",
        ]
        for suid in suids:
            station_name = snapshot["station_cache"].get(suid, "")
            if station_name:
                lines.append(f"{suid} | {station_name}")
            else:
                lines.append(suid)
        return "\n".join(lines)

    async def _handle_charge_enable(self, event: AstrMessageEvent) -> str:
        await self._ensure_state_loaded()
        async with self._state_lock:
            self._state["monitor_enabled"] = True
            self._state["monitor_target_umo"] = str(
                getattr(event, "unified_msg_origin", "") or ""
            )
            self._state["monitor_self_id"] = str(
                getattr(event.message_obj, "self_id", "") or "0"
            )
            await self._persist_state_locked()
        self._monitor_wakeup.set()
        return "监听模式已开启。后台将每 5 分钟检查一次监听列表。"

    async def _handle_charge_disable(self) -> str:
        await self._ensure_state_loaded()
        async with self._state_lock:
            self._state["monitor_enabled"] = False
            await self._persist_state_locked()
        self._monitor_wakeup.set()
        return "监听模式已关闭。"

    async def _prepare_charge_all(
        self,
        event: AstrMessageEvent,
        suid: str,
    ) -> tuple[str, Any]:
        suid = suid.strip()
        if not suid:
            return ("error", "用法：/chargeall <suid>")
        if not _looks_like_suid(suid):
            return (
                "error",
                "chargeall 只支持直接传 suid，例如：/chargeall 401011062900460",
            )

        try:
            result = await self._check_target(suid)
            messages = _build_charge_full_messages(
                result["detail_json"],
                result["profile_json"],
            )
        except PowerLiberApiError as exc:
            logger.exception("chargeall 查询失败")
            return ("error", f"查询失败：{exc}")

        group_id = str(getattr(event.message_obj, "group_id", "") or "")
        if group_id:
            return ("chains", _build_forward_chains(event, messages))
        return ("messages", messages)

    async def _run_monitor_iteration(self) -> None:
        snapshot = await self._get_state_snapshot()
        if not snapshot["monitor_enabled"]:
            return
        if not snapshot["monitor_target_umo"]:
            return
        if not snapshot["monitor_suids"]:
            return

        lines: list[str] = []
        for suid in snapshot["monitor_suids"]:
            try:
                result = await self._check_target(suid)
            except PowerLiberApiError:
                logger.exception("监听轮询失败: %s", suid)
                continue

            if result["strict_ports"] or result["idle_ports"]:
                lines.append(self._format_charge_result(result, include_suid=True))

        if not lines:
            return

        text = "\n".join(
            [
                f"充电桩监听结果 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                *lines,
            ]
        )
        await self.context.send_message(
            snapshot["monitor_target_umo"], [Comp.Plain(text)]
        )

    async def _monitor_loop(self) -> None:
        try:
            await self._ensure_state_loaded()
            while True:
                try:
                    await self._run_monitor_iteration()
                except asyncio.CancelledError:
                    raise
                except Exception:
                    logger.exception("监听任务执行失败")

                try:
                    await asyncio.wait_for(
                        self._monitor_wakeup.wait(),
                        timeout=MONITOR_INTERVAL_SECONDS,
                    )
                except asyncio.TimeoutError:
                    pass
                finally:
                    self._monitor_wakeup.clear()
        except asyncio.CancelledError:
            return

    def _charge_help_text(self) -> str:
        return "\n".join(
            [
                "用法：",
                "/charge <suid|站点名称正则>",
                "/charge <suid|站点名称正则> <端口号>",
            ]
        )

    @filter.command("charge")
    async def charge(
        self,
        event: AstrMessageEvent,
        arg1: str = "",
        arg2: str = "",
        arg3: str = "",
        arg4: str = "",
        arg5: str = "",
    ):
        """查询空余充电口，并管理监听列表和监听模式。"""

        tail = _extract_command_tail(event.message_str, "charge")
        if not tail:
            tail = " ".join(
                part for part in (arg1, arg2, arg3, arg4, arg5) if part
            ).strip()
        if not tail:
            yield event.plain_result(self._charge_help_text())
            return

        action, _, remainder = tail.partition(" ")
        action_lower = action.lower()
        remainder = remainder.strip()

        if action_lower == "add":
            yield event.plain_result(await self._handle_charge_add(remainder))
            return
        if action_lower == "list":
            yield event.plain_result(await self._handle_charge_list())
            return
        if action_lower == "enable":
            yield event.plain_result(await self._handle_charge_enable(event))
            return
        if action_lower == "disable":
            yield event.plain_result(await self._handle_charge_disable())
            return

        query = tail
        requested_port_number: int | None = None
        if " " in tail:
            maybe_query, maybe_port = tail.rsplit(" ", 1)
            maybe_port = maybe_port.strip()
            if maybe_query.strip() and maybe_port.isdigit():
                requested_port_number = int(maybe_port)
                query = maybe_query.strip()

        suid, error = await self._resolve_query_to_suid(query)
        if error:
            yield event.plain_result(error)
            return

        try:
            result = await self._check_target(suid)
        except PowerLiberApiError as exc:
            logger.exception("charge 查询失败")
            yield event.plain_result(f"查询失败：{exc}")
            return

        if requested_port_number is not None:
            if requested_port_number <= 0:
                yield event.plain_result("端口号必须大于 0。")
                return

            ports = result["profile_json"].get("data", {}).get("port_list", [])
            if not isinstance(ports, list):
                yield event.plain_result("接口未返回有效的端口列表。")
                return

            port = _find_port_by_number(ports, requested_port_number)
            if not port:
                yield event.plain_result(
                    f"{result['station_name']} 不存在 {requested_port_number}号口。"
                )
                return

            header = (
                f"{result['station_name']} | {result['suid']} | "
                f"{requested_port_number}号口"
            )
            yield event.plain_result(_render_section(header, port))
            return

        yield event.plain_result(self._format_charge_result(result))

    @filter.command("chargeall")
    async def charge_all(
        self,
        event: AstrMessageEvent,
        arg1: str = "",
        arg2: str = "",
        arg3: str = "",
        arg4: str = "",
        arg5: str = "",
    ):
        """解析全部 JSON，翻译字段并整体以合并转发发送。"""

        tail = _extract_command_tail(event.message_str, "chargeall")
        if not tail:
            tail = " ".join(
                part for part in (arg1, arg2, arg3, arg4, arg5) if part
            ).strip()
        mode, payload = await self._prepare_charge_all(event, tail)
        if mode == "error":
            yield event.plain_result(payload)
            return
        if mode == "chains":
            for chain in payload:
                yield event.chain_result(chain)
            return

        yield event.plain_result("当前不是群聊，无法使用合并转发，以下改为分段发送。")
        for message in payload:
            yield event.plain_result(message)

    async def terminate(self):
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        await self._api.close()
