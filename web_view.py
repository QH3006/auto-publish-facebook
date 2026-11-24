from web_scripts import get_admin_scripts
def get_admin_html(local_ip: str) -> str:
    scripts = get_admin_scripts()
    return f"""<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Quản Trị Tiệm Sách - Máy Chủ Tự Động</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }} body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background-color: #0d1117; color: #c9d1d9; line-height: 1.5; padding: 20px; }} .container {{ max-width: 1200px; margin: 0 auto; }} header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #30363d; padding-bottom: 15px; margin-bottom: 20px; }} h1 {{ font-size: 20px; color: #58a6ff; font-weight: 600; display: flex; align-items: center; gap: 8px; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px; }} .card {{ background-color: #161b22; border: 1px solid #30363d; border-radius: 6px; padding: 15px; }} .card-title {{ font-size: 12px; color: #8b949e; text-transform: uppercase; font-weight: 600; margin-bottom: 5px; }} .card-value {{ font-size: 22px; color: #f0f6fc; font-weight: 700; }} .card-desc {{ font-size: 12px; color: #8b949e; margin-top: 5px; }} .progress-bar {{ width: 100%; height: 6px; background-color: #21262d; border-radius: 3px; margin-top: 8px; overflow: hidden; }} .progress-fill {{ height: 100%; background-color: #238636; width: 0%; transition: width 0.3s; }}
        .btn {{ background-color: #238636; color: #ffffff; border: 1px solid rgba(240,246,252,0.1); border-radius: 6px; padding: 6px 14px; font-size: 13px; font-weight: 500; cursor: pointer; transition: background 0.2s; }} .btn:hover {{ background-color: #2ea043; }} .btn-outline {{ background-color: #21262d; color: #c9d1d9; border: 1px solid #30363d; }} .btn-outline:hover {{ background-color: #30363d; color: #58a6ff; }} .btn-danger {{ background-color: #da3633; color: #fff; }} .btn-danger:hover {{ background-color: #b62324; }} .btn-sm {{ padding: 3px 8px; font-size: 12px; }}
        .tabs {{ display: flex; border-bottom: 1px solid #30363d; margin-bottom: 15px; gap: 10px; }} .tab-btn {{ background: none; border: none; color: #8b949e; padding: 8px 16px; font-size: 14px; font-weight: 500; cursor: pointer; border-bottom: 2px solid transparent; }} .tab-btn.active {{ color: #58a6ff; border-bottom-color: #58a6ff; }} .tab-content {{ display: none; }} .tab-content.active {{ display: block; }} table {{ width: 100%; border-collapse: collapse; text-align: left; font-size: 13px; }} th, td {{ padding: 10px 12px; border-bottom: 1px solid #21262d; }} th {{ background-color: #161b22; color: #8b949e; font-weight: 600; }} tr:hover {{ background-color: #161b22; }}
        .badge {{ display: inline-block; padding: 2px 6px; border-radius: 12px; font-size: 11px; font-weight: 600; text-align: center; }} .badge-available {{ background: rgba(35, 134, 54, 0.2); color: #3fb950; border: 1px solid #238636; }} .badge-sold {{ background: rgba(218, 54, 51, 0.2); color: #f85149; border: 1px solid #da3633; }} .badge-pending {{ background: rgba(210, 153, 34, 0.2); color: #d29922; border: 1px solid #d29922; }} .badge-approved {{ background: rgba(56, 139, 253, 0.2); color: #58a6ff; border: 1px solid #388bfd; }} .badge-cat {{ background: #21262d; color: #58a6ff; border: 1px solid #30363d; border-radius: 4px; padding: 2px 6px; }} .thumb {{ width: 44px; height: 60px; object-fit: cover; border-radius: 4px; border: 1px solid #30363d; cursor: pointer; }} .modal {{ display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.75); z-index: 1000; align-items: center; justify-content: center; }} .modal.open {{ display: flex; }} .modal-box {{ background: #161b22; border: 1px solid #30363d; border-radius: 8px; width: 560px; max-width: 95%; padding: 20px; color: #c9d1d9; max-height: 90vh; overflow-y: auto; }} .modal-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; border-bottom: 1px solid #30363d; padding-bottom: 10px; }} .modal-title {{ font-size: 16px; font-weight: 600; color: #58a6ff; }} .close-btn {{ background: none; border: none; color: #8b949e; font-size: 20px; cursor: pointer; }} .form-group {{ margin-bottom: 12px; }} .form-label {{ display: block; font-size: 12px; color: #8b949e; margin-bottom: 4px; font-weight: 500; }} .form-input {{ width: 100%; background: #0d1117; border: 1px solid #30363d; color: #c9d1d9; padding: 6px 10px; border-radius: 6px; font-size: 13px; }} .form-input:focus {{ outline: none; border-color: #58a6ff; }} .modal-footer {{ display: flex; justify-content: flex-end; gap: 8px; margin-top: 15px; border-top: 1px solid #30363d; padding-top: 12px; }} .preview-img {{ max-width: 100%; max-height: 200px; object-fit: contain; border-radius: 6px; margin-bottom: 10px; border: 1px solid #30363d; background: #0d1117; }} .toolbar {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; flex-wrap: wrap; gap: 10px; }} .filter-group {{ display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }} .cat-chip {{ display: inline-flex; align-items: center; gap: 6px; background: #21262d; border: 1px solid #30363d; border-radius: 16px; padding: 4px 10px; font-size: 12px; margin: 3px; color: #58a6ff; }} .price-range-box {{ display: none; align-items: center; gap: 6px; background: #161b22; border: 1px solid #30363d; border-radius: 6px; padding: 3px 10px; }} .price-range-box:focus-within {{ border-color: #58a6ff; }} .pr-lbl {{ font-size: 12px; color: #8b949e; user-select: none; }} .pr-inp {{ width: 88px; background: #0d1117; border: 1px solid #30363d; border-radius: 4px; color: #58a6ff; font-size: 13px; font-weight: 600; text-align: right; outline: none; padding: 2px 6px; }} .pr-inp:focus {{ border-color: #58a6ff; }} .pr-inp::placeholder {{ color: #484f58; font-weight: 400; font-size: 11px; }} .pr-sep {{ color: #8b949e; font-size: 12px; }} .pr-unit {{ font-size: 12px; color: #8b949e; font-weight: 600; }}
        .pagination-bar {{ display: flex; justify-content: center; align-items: center; gap: 6px; margin-top: 14px; flex-wrap: wrap; }} .page-btn {{ background: #21262d; color: #c9d1d9; border: 1px solid #30363d; border-radius: 6px; padding: 5px 11px; font-size: 13px; cursor: pointer; transition: all 0.15s; }} .page-btn:hover:not(:disabled) {{ background: #30363d; color: #58a6ff; border-color: #58a6ff; }} .page-btn.active {{ background: #1f6feb; color: #ffffff; border-color: #58a6ff; font-weight: 600; }} .page-btn:disabled {{ opacity: 0.4; cursor: not-allowed; }} .page-ellipsis {{ color: #8b949e; padding: 0 4px; font-size: 13px; }} .page-info {{ font-size: 12px; color: #8b949e; margin-left: 8px; }}
    </style>
</head>
<body>
<div class="container">
    <header>
        <div>
            <h1>📖 Quản Trị Hệ Thống Tiệm Sách Của Thương</h1>
            <p class="card-desc">Máy chủ nội bộ: <code>http://{local_ip}:8080</code> | RAM tiêu thụ: ~10MB</p>
        </div>
        <div style="display:flex; gap:8px;">
            <button class="btn btn-outline" onclick="openCatModal()">🏷️ Thể Loại</button>
            <button class="btn btn-outline" onclick="openAddModal()">➕ Thêm Sách (Đơn / Hàng Loạt)</button>
            <button class="btn" onclick="approveAllPending()">✅ Duyệt Tất Cả Sách Chờ</button>
        </div>
    </header>
    <div class="grid">
        <div class="card"><div class="card-title">Bộ Nhớ RAM</div><div class="card-value" id="ram-val">-- GB</div><div class="card-desc" id="ram-desc">Đang tải...</div><div class="progress-bar"><div class="progress-fill" id="ram-bar"></div></div></div><div class="card"><div class="card-title">Vi Xử Lý CPU</div><div class="card-value" id="cpu-val">-- %</div><div class="card-desc">Tải CPU hệ thống</div><div class="progress-bar"><div class="progress-fill" id="cpu-bar"></div></div></div><div class="card"><div class="card-title">Ổ Cứng Lưu Trữ</div><div class="card-value" id="disk-val">-- GB</div><div class="card-desc" id="disk-desc">Dung lượng ổ đĩa</div><div class="progress-bar"><div class="progress-fill" id="disk-bar"></div></div></div>
        <div class="card"><div class="card-title">Card Đồ Họa GPU</div><div class="card-value" id="gpu-val" style="font-size: 15px; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">--</div><div class="card-desc" id="gpu-desc">Mức tải GPU</div><div class="progress-bar"><div class="progress-fill" id="gpu-bar"></div></div></div><div class="card"><div class="card-title">Kho Sách Còn Hàng</div><div class="card-value" id="stock-val">--</div><div class="card-desc">Cuốn sẵn sàng bán</div></div><div class="card"><div class="card-title">Sách Đã Bán / Khách Hỏi</div><div class="card-value" id="sold-val">-- / --</div><div class="card-desc">Đã bán / Lead chờ trả lời</div></div><div class="card"><div class="card-title">Trạng Thái AI & Token</div><div class="card-value" id="ai-val" style="font-size: 15px;">--</div><div class="card-desc" id="ai-desc">Đang kiểm tra...</div></div>
    </div>
    <div class="tabs">
        <button class="tab-btn active" onclick="switchTab('tab-books')">📚 Quản Lý Kho Sách</button>
        <button class="tab-btn" onclick="switchTab('tab-leads')">💬 Khách Hỏi Mua (Leads)</button>
    </div>
    <div id="tab-books" class="tab-content active">
        <div class="toolbar">
            <div class="filter-group">
                <input type="text" id="search-input" class="form-input" style="width: 175px;" placeholder="🔍 Tìm ID, tên sách..." oninput="renderTable(true)"><select id="category-filter" class="form-input" style="width: 145px;" onchange="renderTable(true)"><option value="">Tất cả thể loại</option></select><select id="price-filter" class="form-input" style="width: 135px;" onchange="onPriceFilterChange()"><option value="">Tất cả mức giá</option><option value="0-50000">&lt; 50.000 đ</option><option value="50000-100000">50k - 100k</option><option value="100000-150000">100k - 150k</option><option value="150000-99999999">&gt; 150.000 đ</option><option value="no_price">Chưa có giá</option><option value="custom">Tùy chỉnh giá...</option></select><div id="custom-price-box" class="price-range-box"><span class="pr-lbl">Từ</span><input type="text" inputmode="numeric" id="min-price-input" class="pr-inp" placeholder="35k / 35.000" oninput="onCustomPriceInput(this)"><span class="pr-sep">—</span><span class="pr-lbl">Đến</span><input type="text" inputmode="numeric" id="max-price-input" class="pr-inp" placeholder="50k / 50.000" oninput="onCustomPriceInput(this)"><span class="pr-unit">đ</span></div><select id="status-filter" class="form-input" style="width: 125px;" onchange="renderTable(true)"><option value="">Tất cả trạng thái</option><option value="available">Còn hàng</option><option value="sold_out">Đã bán</option><option value="pending_review">Chờ soát</option></select><select id="sort-filter" class="form-input" style="width: 135px;" onchange="renderTable(true)"><option value="id_desc">Mới nhất (#ID ↓)</option><option value="id_asc">Cũ nhất (#ID ↑)</option><option value="price_asc">Giá tăng dần</option><option value="price_desc">Giá giảm dần</option><option value="title_asc">Tên sách (A-Z)</option></select><button class="btn btn-outline btn-sm" onclick="resetFilters()" title="Đặt lại bộ lọc">❌ Đặt lại</button>
            </div>
            <div style="font-size:12px; color:#8b949e;" id="count-info">Hiển thị: 0 cuốn</div>
        </div>
        <div class="card" style="padding:0; overflow-x:auto;">
            <table>
                <thead><tr><th style="width: 40px;">#ID</th><th style="width: 60px;">Bìa</th><th>Tựa Sách & Tác Giả</th><th style="width: 140px;">Thể Loại</th><th style="width: 110px;">Giá Bán</th><th style="width: 110px;">Trạng Thái</th><th style="width: 110px;">Kiểm Soát</th><th style="width: 130px; text-align:center;">Thao Tác</th></tr></thead>
                <tbody id="books-tbody"><tr><td colspan="8" style="text-align:center; padding: 20px;">Đang tải dữ liệu kho sách...</td></tr></tbody>
            </table>
        </div>
        <div id="pagination-bar" class="pagination-bar"></div>
    </div>
    <div id="tab-leads" class="tab-content">
        <div class="toolbar">
            <div class="filter-group">
                <select id="lead-status-filter" class="form-input" style="width: 160px;" onchange="renderLeads()">
                    <option value="">Tất cả trạng thái</option><option value="pending">Chờ phản hồi</option><option value="contacted">Đã liên hệ</option>
                </select>
                <button class="btn btn-outline btn-sm" onclick="fetchLeads()">🔄 Tải lại</button>
            </div>
            <div style="font-size:12px; color:#8b949e;" id="lead-count-info">Cơ hội: 0 bài viết</div>
        </div>
        <div class="card" style="padding:0; overflow-x:auto;">
            <table>
                <thead><tr><th style="width: 70px;">#ID</th><th style="width: 220px;">Sách Khớp Kho</th><th>Nội Dung Bài Đăng (Khách Hỏi)</th><th style="width: 120px;">Trạng Thái</th><th style="width: 200px; text-align:center;">Thao Tác</th></tr></thead>
                <tbody id="leads-tbody"><tr><td colspan="5" style="text-align:center; padding: 20px;">Đang tải dữ liệu khách tìm mua...</td></tr></tbody>
            </table>
        </div>
    </div>
</div>
<div id="edit-modal" class="modal">
    <div class="modal-box">
        <div class="modal-header"><div class="modal-title">✏️ Chỉnh Sửa & Soát Lại Thông Tin Sách</div><button class="close-btn" onclick="closeModal('edit-modal')">&times;</button></div>
        <div style="text-align:center;"><img id="m-preview" src="" class="preview-img" alt="Bìa sách"></div>
        <input type="hidden" id="m-id">
        <div class="form-group"><label class="form-label">Tựa Sách</label><input type="text" id="m-title" class="form-input"></div>
        <div class="form-group"><label class="form-label">Tác Giả</label><input type="text" id="m-author" class="form-input"></div>
        <div class="form-group"><div style="display:flex; justify-content:space-between; align-items:center;"><label class="form-label">Thể Loại Sách</label><a href="javascript:void(0)" onclick="openCatModal()" style="font-size:11px; color:#58a6ff; text-decoration:none;">+ Quản lý thể loại</a></div><select id="m-category" class="form-input"></select></div>
        <div class="form-group"><label class="form-label">Giá Bán (VNĐ)</label><input type="text" id="m-price" class="form-input" placeholder="Ví dụ: 35000"></div>
        <div class="form-group"><label class="form-label">Trạng Thái Kho</label><select id="m-status" class="form-input"><option value="available">Còn hàng</option><option value="sold_out">Đã bán</option></select></div>
        <div class="modal-footer"><button class="btn btn-danger btn-sm" onclick="deleteCurrentBook()">🗑️ Xóa Sách</button><div style="flex:1;"></div><button class="btn btn-outline btn-sm" style="color:#3fb950; border-color:#238636;" onclick="quickApproveFromModal()">✅ Đã Soát Xong</button><button class="btn btn-outline" onclick="closeModal('edit-modal')">Hủy</button><button class="btn" onclick="saveBookEdit()">💾 Lưu</button></div>
    </div>
</div>
<div id="add-modal" class="modal">
    <div class="modal-box">
        <div class="modal-header"><div class="modal-title">➕ Thêm Sách (Hỗ Trợ Chọn Nhiều Ảnh Cùng Lúc)</div><button class="close-btn" onclick="closeModal('add-modal')">&times;</button></div>
        <div class="form-group"><label class="form-label">📸 Ảnh Bìa (Chọn 1 hoặc nhiều ảnh cùng lúc, AI tự nhận diện):</label><input type="file" id="add-cover-file" class="form-input" accept="image/*" multiple onchange="handleCoverUpload(event)"><div id="add-ai-status" style="font-size:12px; margin-top:4px; display:none;"></div><div id="batch-info" style="display:none; padding:10px; background:#21262d; border-radius:6px; margin-top:8px; font-size:13px; color:#58a6ff;"></div><div style="text-align:center; margin-top:6px;"><img id="add-preview-img" style="display:none; max-height:130px; border-radius:6px; border:1px solid #30363d;" alt="Bìa sách"></div></div>
        <div id="single-fields">
            <div class="form-group"><label class="form-label">Tựa Sách (*)</label><input type="text" id="add-title" class="form-input" placeholder="Nhập tên sách chính xác"></div>
            <div class="form-group"><label class="form-label">Tác Giả</label><input type="text" id="add-author" class="form-input" placeholder="Tên tác giả hoặc dịch giả"></div>
        </div>
        <div class="form-group"><div style="display:flex; justify-content:space-between; align-items:center;"><label class="form-label">Thể Loại Sách</label><a href="javascript:void(0)" onclick="openCatModal()" style="font-size:11px; color:#58a6ff; text-decoration:none;">+ Quản lý thể loại</a></div><select id="add-category" class="form-input"></select></div>
        <div class="form-group"><label class="form-label">Giá Bán (VNĐ)</label><input type="text" id="add-price" class="form-input" placeholder="Ví dụ: 50000 hoặc 50k (để trống nếu muốn AI tự đọc)"></div>
        <div class="form-group"><label class="form-label">Trạng Thái</label><select id="add-status" class="form-input"><option value="available">Còn hàng</option><option value="sold_out">Đã bán</option></select></div>
        <div class="modal-footer"><button class="btn btn-outline" onclick="closeModal('add-modal')">Hủy</button><button class="btn" id="add-submit-btn" onclick="submitAddBook()">➕ Thêm Vào Kho</button></div>
    </div>
</div>
<div id="cat-modal" class="modal">
    <div class="modal-box" style="width: 480px;">
        <div class="modal-header"><div class="modal-title">🏷️ Quản Lý Danh Mục Thể Loại</div><button class="close-btn" onclick="closeModal('cat-modal')">&times;</button></div>
        <div style="display:flex; gap:8px; margin-bottom:12px;"><input type="text" id="new-cat-name" class="form-input" placeholder="Tên thể loại mới (ví dụ: Trinh thám, Kinh dị...)"><button class="btn btn-sm" onclick="submitAddCategory()" style="white-space:nowrap;">➕ Thêm</button></div>
        <div class="form-label" style="margin-bottom:6px;">Danh sách thể loại hiện có:</div>
        <div id="cat-list-container" style="display:flex; flex-wrap:wrap; max-height:220px; overflow-y:auto; padding:6px; background:#0d1117; border:1px solid #30363d; border-radius:6px;"></div>
        <div class="modal-footer"><button class="btn btn-outline btn-sm" onclick="closeModal('cat-modal')">Đóng</button></div>
    </div>
</div>
<script>
{scripts}
</script>
</body>
</html>"""
