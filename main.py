import json
import time

import requests

from logger import logger

from config_rts import load_config
from constant import BASE_API_URL, PORTAL_LOGIN_URL, ABSTRACT_QUEUE_URL
from utils import get_token
from ts_portal import TS


config = load_config()



if __name__ == "__main__":
    while True:
        ts = None
        try:
            logger.info("Starting cycle")

            url = f"{BASE_API_URL}/pps_delivery_orders/"
            headers = {"content-type": "application/json", "Authorization": "Token " + get_token()}
            response = requests.get(url, headers=headers)
            orderObj = json.loads(response.content)

            orders = {"account1": [], "account2": []}

    
            restrict_count = 0
            for key in orderObj:
                if restrict_count > 25:
                    break

                o = orderObj[key]

                if o["search_pd_St_dt"] == "":
                    o["search_pd_St_dt"] = " "

                if all(v != "" for v in o.values()):
                    order_unit = [
                        o["client_ref"], o["pdf"], o["effective_date"],
                        o["search_pd_St_dt"], o["borrower_name_in_the_title"]
                    ]

                    if o["product"] == "Prior Policy Search":
                        if o["state"] == "GA":
                            order_unit.append("Yes")
                        elif o["note_type"] in ["No New Docs", "Expected Docs"]:
                            order_unit.append("No")
                        else:
                            order_unit.append("Yes")
                    elif o["product"] == "PPS Update":
                        order_unit.append(o["only_eff_dt_changed"])
                    else:
                        order_unit.append(o["is_developer_deed"])

                    order_unit.append(o["product"])
                    order_unit.append(key)
                    order_unit.append((o["county"], o["state"]))

                    if o["product"] == "Prior Policy Search":
                        if not o["note_type"]:
                            if o["new_pps_recordings_found"] == "No":
                                order_unit.append(
                                    "We only found 2 expected new documents: a release of the prior subject mortgage and a new Rocket mortgage."
                                )
                            else:
                                order_unit.append("*New recordings found, please see attached.")
                        else:
                            if o["note_type"] == "No New Docs":
                                order_unit.append("No New documents have been found.")
                            elif o["note_type"] == "Expected Docs":
                                order_unit.append(
                                    "We only found 2 expected new documents: a release of the prior subject mortgage and a new Rocket mortgage."
                                )
                            else:
                                order_unit.append("*New recordings found, please see attached.")
                    else:
                        if o["new_pps_recordings_found"] == "No":
                            order_unit.append("No New documents have been found.")
                        else:
                            order_unit.append("*New recordings found, please see attached.")

                    try:
                        orders[o["ts_identifier"].replace(" ", "").lower()].append(order_unit)
                    except:
                        pass

                    restrict_count += 1

            # ACCOUNT 1
            if orders["account1"]:
                ts = None
                try:
                    print("after build")
                    ts = TS({
                        "username": config["PPS_ACC_1_USERNAME"],
                        "password": config["PPS_ACC_1_PASSWORD"],
                        "orders": orders["account1"],
                    })
                    logger.info("login started")
                    ts.login(True, config["PPS_MFA"])
                    ts.search_order()
                except Exception as e:
                    logger.exception("ACCOUNT 1 ERROR:", str(e))
                    if ts:
                        ts.quit()
                    continue 
                finally:
                    if ts:
                        ts.quit()
            else:
                logger.info("No orders for account1")

            # ACCOUNT 2 
            if orders["account2"]:
                ts = None
                try:
                    ts = TS({
                        "username": config["PPS_ACC_2_USERNAME"],
                        "password": config["PPS_ACC_2_PASSWORD"],
                        "orders": orders["account2"],
                    })
                    ts.login()
                    ts.search_order()
                except Exception as e:
                    logger.exception("ACCOUNT 2 ERROR:", str(e))
                    if ts:
                        ts.quit()
                finally:
                    if ts:
                        ts.quit()
            else:
                logger.info("No orders for account2")
                


            logger.info("Cycle done. Sleeping 60s\n")
            time.sleep(60)
           

        except Exception as e:
            logger.exception("Unexpected error in main loop:")
