from flask import render_template, request
from db.db import DBConnection
from __main__ import app 

@app.route('/library')
def library():
    search_query = request.args.get('search', '')  # default is empty if not provided
    page = int(request.args.get('page', 1))  # default page is 1 if not provided
    sort_order = request.args.get('sort', 'desc')  # Default to descending (newest first)
    items_per_page = 8
    offset = (page - 1) * items_per_page

    sql_query = """
        SELECT p.*, COUNT(s.userid) AS star_count
        FROM Prompts p
        LEFT JOIN Stars s ON p.PromptID = s.promptid
        WHERE p.PromptTitle LIKE ? 
        GROUP BY p.PromptID 
        """ 
    
    if sort_order == 'asc':
        sql_query += "ORDER BY PromptID ASC "
    else: 
        sql_query += "ORDER BY PromptID DESC "
    sql_query += "LIMIT ? OFFSET ?"
    search_pattern = f'%{search_query}%'

    total_prompts_query = "SELECT COUNT(*) FROM Prompts WHERE PromptTitle LIKE ?"

    with DBConnection() as cursor:
        cursor.execute(sql_query, (search_pattern, items_per_page, offset))
        prompts = cursor.fetchall()

        cursor.execute(total_prompts_query, (search_pattern,))
        total_prompts = cursor.fetchone()[0]
    
    total_pages = (total_prompts + items_per_page - 1) // items_per_page  # Rounds up

    return render_template('library.html', prompts=prompts, search_query=search_query,
                           current_page=page, total_pages=total_pages, sort_order=sort_order)