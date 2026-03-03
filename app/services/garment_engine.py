from app.services.print_sheet_engine import generate_print_sheet

def process_garment(size, artwork_path, fabric_type):

    result = generate_print_sheet(size, artwork_path, fabric_type)

    return result