from server import app

def print_routes():
    print("Listing all registered routes:")
    for rule in app.url_map.iter_rules():
        print(f"{rule} {rule.methods}")

if __name__ == "__main__":
    print_routes()
