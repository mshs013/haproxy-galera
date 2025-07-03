#!/usr/bin/env python3
import json
import socket
import threading
import time
import MySQLdb

proc_end = False
debug = True
checkFlowcontrol = False

healthyGalera = {
    'wsrep_cluster_status': 'Primary',
    'wsrep_connected': 'ON',
    'wsrep_local_state_comment': 'Synced',
    'wsrep_ready': 'ON',
    'read_only': 'OFF',
}


def log(message, always=False):
    if always or debug:
        thread = threading.current_thread()
        print(f"[{thread.name}] {message}")


def get_status(result):
    available = '200 OK'
    unavailable = '503 Service Unavailable'
    for key, value in healthyGalera.items():
        if result.get(key) != value:
            return unavailable
    if checkFlowcontrol and float(result.get('wsrep_flow_control_paused', 0)) > 0.8:
        return unavailable
    return available


def check_database():
    result = {}
    try:
        db = MySQLdb.connect(
            host="localhost",
            user="haproxy_check",
            passwd=""
        )
        cur = db.cursor()
        for query in [
            "SHOW VARIABLES LIKE 'read_only'",
            "SHOW STATUS LIKE '%wsrep%'",
        ]:
            cur.execute(query)
            for row in cur.fetchall():
                result[row[0]] = row[1]
        db.close()
    except Exception as e:
        log(f"MySQL check failed: {e}", True)
    return result


def handle_connection(conn, addr):
    log(f"Connection from {addr}", True)
    db_status = check_database()
    message = json.dumps({'status': db_status})
    response = (
        "HTTP/1.1 " + get_status(db_status) +
        "\r\nContent-Type: application/json" +
        "\r\nConnection: close" +
        f"\r\nContent-Length: {len(message)}" +
        "\r\n\r\n" + message + "\n"
    )
    try:
        conn.sendall(response.encode())
        time.sleep(0.01)  # 👈 Ensure data is flushed before shutdown
        conn.shutdown(socket.SHUT_RDWR)  # 👈 graceful shutdown
    except Exception as e:
        log(f"Error sending or closing: {e}", True)
    finally:
        conn.close()


def main():
    TCP_IP = '0.0.0.0'
    TCP_PORT = 9200

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((TCP_IP, TCP_PORT))
    server.listen(5)
    log(f"Monitoring agent listening on {TCP_IP}:{TCP_PORT}", True)

    try:
        while not proc_end:
            conn, addr = server.accept()
            threading.Thread(target=handle_connection, args=(conn, addr), daemon=True).start()
    except KeyboardInterrupt:
        log("Shutting down...")
    finally:
        server.close()


if __name__ == "__main__":
    main()
