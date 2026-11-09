def get_admin_html(local_ip: str) -> str:
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
        .badge {{ display: inline-block; padding: 2px 6px; border-radius: 12px; font-size: 11px; font-weight: 600; text-align: center; }} .badge-available {{ background: rgba(35, 134, 54, 0.2); color: #3fb950; border: 1px solid #238636; }} .badge-sold {{ background: rgba(218, 54, 51, 0.2); color: #f85149; border: 1px solid #da3633; }} .badge-pending {{ background: rgba(210, 153, 34, 0.2); color: #d29922; border: 1px solid #d29922; }} .badge-approved {{ background: rgba(56, 139, 253, 0.2); color: #58a6ff; border: 1px solid #388bfd; }} .badge-cat {{ background: #21262d; color: #58a6ff; border: 1px solid #30363d; border-radius: 4px; padding: 2px 6px; }} .thumb {{ width: 44px; height: 60px; object-fit: cover; border-radius: 4px; border: 1px solid #30363d; cursor: pointer; }} .modal {{ display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.75); z-index: 1000; align-items: center; justify-content: center; }} .modal.open {{ display: flex; }} .modal-box {{ background: #161b22; border: 1px solid #30363d; border-radius: 8px; width: 560px; max-width: 95%; padding: 20px; color: #c9d1d9; max-height: 90vh; overflow-y: auto; }} .modal-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; border-bottom: 1px solid #30363d; padding-bottom: 10px; }} .modal-title {{ font-size: 16px; font-weight: 600; color: #58a6ff; }} .close-btn {{ background: none; border: none; color: #8b949e; font-size: 20px; cursor: pointer; }} .form-group {{ margin-bottom: 12px; }} .form-label {{ display: block; font-size: 12px; color: #8b949e; margin-bottom: 4px; font-weight: 500; }} .form-input {{ width: 100%; background: #0d1117; border: 1px solid #30363d; color: #c9d1d9; padding: 6px 10px; border-radius: 6px; font-size: 13px; }} .form-input:focus {{ outline: none; border-color: #58a6ff; }} .modal-footer {{ display: flex; justify-content: flex-end; gap: 8px; margin-top: 15px; border-top: 1px solid #30363d; padding-top: 12px; }} .preview-img {{ max-width: 100%; max-height: 200px; object-fit: contain; border-radius: 6px; margin-bottom: 10px; border: 1px solid #30363d; background: #0d1117; }} .toolbar {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; flex-wrap: wrap; gap: 10px; }} .filter-group {{ display: flex; gap: 8px; align-items: center; }} .cat-chip {{ display: inline-flex; align-items: center; gap: 6px; background: #21262d; border: 1px solid #30363d; border-radius: 16px; padding: 4px 10px; font-size: 12px; margin: 3px; color: #58a6ff; }}
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
        <div class="card"><div class="card-title">Card Đồ Họa GPU</div><div class="card-value" id="gpu-val" style="font-size: 15px; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">--</div><div class="card-desc" id="gpu-desc">Mức tải GPU</div><div class="progress-bar"><div class="progress-fill" id="gpu-bar"></div></div></div><div class="card"><div class="card-title">Kho Sách Còn Hàng</div><div class="card-value" id="stock-val">--</div><div class="card-desc">Cuốn sẵn sàng bán</div></div><div class="card"><div class="card-title">Sách Đã Bán / Khách Hỏi</div><div class="card-value" id="sold-val">-- / --</div><div class="card-desc">Đã bán / Lead chờ trả lời</div></div>
    </div>
    <div class="tabs">
        <button class="tab-btn active" onclick="switchTab('tab-books')">📚 Quản Lý Kho Sách</button>
        <button class="tab-btn" onclick="switchTab('tab-leads')">💬 Khách Hỏi Mua (Leads)</button>
    </div>
    <div id="tab-books" class="tab-content active">
        <div class="toolbar">
            <div class="filter-group">
                <input type="text" id="search-input" class="form-input" style="width: 175px;" placeholder="🔍 Tìm ID, tên sách..." oninput="renderTable()"><select id="category-filter" class="form-input" style="width: 145px;" onchange="renderTable()"><option value="">Tất cả thể loại</option></select><select id="price-filter" class="form-input" style="width: 135px;" onchange="onPriceFilterChange()"><option value="">Tất cả mức giá</option><option value="0-50000">&lt; 50.000 đ</option><option value="50000-100000">50k - 100k</option><option value="100000-150000">100k - 150k</option><option value="150000-99999999">&gt; 150.000 đ</option><option value="custom">Tùy chỉnh giá...</option></select><input type="number" id="min-price-input" class="form-input" style="width: 75px; display:none;" placeholder="Từ đ" oninput="renderTable()"><input type="number" id="max-price-input" class="form-input" style="width: 75px; display:none;" placeholder="Đến đ" oninput="renderTable()"><select id="status-filter" class="form-input" style="width: 125px;" onchange="renderTable()"><option value="">Tất cả trạng thái</option><option value="available">Còn hàng</option><option value="sold_out">Đã bán</option><option value="pending_review">Chờ soát</option></select><select id="sort-filter" class="form-input" style="width: 135px;" onchange="renderTable()"><option value="id_desc">Mới nhất (#ID ↓)</option><option value="id_asc">Cũ nhất (#ID ↑)</option><option value="price_asc">Giá tăng dần</option><option value="price_desc">Giá giảm dần</option><option value="title_asc">Tên sách (A-Z)</option></select><button class="btn btn-outline btn-sm" onclick="resetFilters()" title="Đặt lại bộ lọc">❌ Đặt lại</button>
            </div>
            <div style="font-size:12px; color:#8b949e;" id="count-info">Hiển thị: 0 cuốn</div>
        </div>
        <div class="card" style="padding:0; overflow-x:auto;">
            <table>
                <thead><tr><th style="width: 40px;">#ID</th><th style="width: 60px;">Bìa</th><th>Tựa Sách & Tác Giả</th><th style="width: 140px;">Thể Loại</th><th style="width: 110px;">Giá Bán</th><th style="width: 110px;">Trạng Thái</th><th style="width: 110px;">Kiểm Soát</th><th style="width: 130px; text-align:center;">Thao Tác</th></tr></thead>
                <tbody id="books-tbody"><tr><td colspan="8" style="text-align:center; padding: 20px;">Đang tải dữ liệu kho sách...</td></tr></tbody>
            </table>
        </div>
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
let allBooks = [];
function switchTab(tabId) {{
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    event.currentTarget.classList.add('active');
    document.getElementById(tabId).classList.add('active');
    if (tabId === 'tab-leads') fetchLeads();
}}
function closeModal(id) {{ document.getElementById(id).classList.remove('open'); }}
let addCoverBase64 = '', selectedFiles = [];
function openAddModal() {{
    addCoverBase64 = ''; selectedFiles = [];
    ['add-title', 'add-author', 'add-price', 'add-cover-file'].forEach(id => {{ let el = document.getElementById(id); if (el) el.value = ''; }});
    document.getElementById('add-category').value = '';
    document.getElementById('single-fields').style.display = 'block';
    let prev = document.getElementById('add-preview-img'); if (prev) {{ prev.src = ''; prev.style.display = 'none'; }}
    let st = document.getElementById('add-ai-status'); if (st) {{ st.innerText = ''; st.style.display = 'none'; }}
    let bi = document.getElementById('batch-info'); if (bi) bi.style.display = 'none';
    let btn = document.getElementById('add-submit-btn'); if (btn) {{ btn.innerText = '➕ Thêm Vào Kho'; btn.disabled = false; }}
    document.getElementById('add-modal').classList.add('open');
}}
function handleCoverUpload(event) {{
    let files = event.target.files;
    if (!files || files.length === 0) return;
    selectedFiles = Array.from(files);
    let st = document.getElementById('add-ai-status'), prev = document.getElementById('add-preview-img'), sFields = document.getElementById('single-fields'), bInfo = document.getElementById('batch-info'), btn = document.getElementById('add-submit-btn');
    if (selectedFiles.length === 1) {{
        sFields.style.display = 'block'; bInfo.style.display = 'none'; btn.innerText = '➕ Thêm Vào Kho';
        let reader = new FileReader();
        reader.onload = function(e) {{
            addCoverBase64 = e.target.result;
            if (prev) {{ prev.src = addCoverBase64; prev.style.display = 'inline-block'; }}
            if (st) {{ st.style.display = 'block'; st.style.color = '#58a6ff'; st.innerText = '⏳ Đang gọi Gemini AI đọc bìa sách...'; }}
            fetch('/api/analyze-cover', {{ method: 'POST', headers: {{ 'Content-Type': 'application/json' }}, body: JSON.stringify({{ image_base64: addCoverBase64 }}) }})
            .then(r => r.json()).then(res => {{
                if (res.success) {{
                    if (res.title) document.getElementById('add-title').value = res.title;
                    if (res.author) document.getElementById('add-author').value = res.author;
                    if (res.category) {{ let catSel = document.getElementById('add-category'); if (catSel && !Array.from(catSel.options).some(o => o.value === res.category)) {{ let opt = document.createElement('option'); opt.value = res.category; opt.innerText = res.category; catSel.appendChild(opt); }} if (catSel) catSel.value = res.category; }}
                    if (res.price) document.getElementById('add-price').value = res.price;
                    if (st) {{ st.style.color = '#3fb950'; st.innerText = '✅ AI đã nhận diện xong! Có thể sửa lại nếu cần.'; }}
                }} else {{ if (st) {{ st.style.color = '#d29922'; st.innerText = '⚠️ Không nhận diện rõ, vui lòng tự điền.'; }} }}
            }}).catch(() => {{ if (st) {{ st.style.color = '#f85149'; st.innerText = '❌ Lỗi đọc ảnh, hãy tự điền thủ công.'; }} }});
        }};
        reader.readAsDataURL(selectedFiles[0]);
    }} else {{
        sFields.style.display = 'none'; if (prev) prev.style.display = 'none'; if (st) st.style.display = 'none';
        bInfo.style.display = 'block';
        bInfo.innerHTML = `📸 <b>Đã chọn ${{selectedFiles.length}} ảnh bìa sách.</b><br><span style="color:#8b949e; font-size:12px;">Hệ thống sẽ nạp từng ảnh, gọi AI đọc tên/tác giả/thể loại/giá và thêm vào kho (trạng thái Chờ Soát để duyệt lại). Bạn có thể đặt giá hoặc thể loại chung bên dưới (hoặc để trống cho AI tự đọc).</span>`;
        btn.innerText = `🚀 Tải Lên & Nhận Diện Hàng Loạt (${{selectedFiles.length}} cuốn)`;
    }}
}}
function parsePriceInput(val) {{
    if (!val) return "";
    let s = String(val).toLowerCase().replace(/[^0-9k]/g, '').trim();
    if (s.endsWith('k')) {{ let n = parseInt(s.slice(0, -1)); return isNaN(n) ? "" : String(n * 1000); }}
    let n = parseInt(s);
    return isNaN(n) ? "" : (n < 1000 && n > 0 ? String(n * 1000) : String(n));
}}
function formatPrice(price) {{
    return (!price || isNaN(parseInt(price))) ? '<span style="color:#8b949e">Chưa có giá</span>' : Number(price).toLocaleString('vi-VN') + ' đ';
}}
function fetchMetrics() {{
    fetch('/api/metrics').then(r => r.json()).then(d => {{
        document.getElementById('ram-val').innerText = d.ram_used_gb + ' / ' + d.ram_total_gb + ' GB';
        document.getElementById('ram-desc').innerText = 'Đang dùng: ' + d.ram_percent + '%';
        document.getElementById('ram-bar').style.width = d.ram_percent + '%';
        document.getElementById('cpu-val').innerText = d.cpu_percent + ' %';
        document.getElementById('cpu-bar').style.width = Math.min(d.cpu_percent, 100) + '%';
        if (d.disk_used_gb) {{
            document.getElementById('disk-val').innerText = d.disk_used_gb + ' / ' + d.disk_total_gb + ' GB';
            document.getElementById('disk-desc').innerText = 'Trống: ' + d.disk_free_gb + ' GB (' + d.disk_percent + '%)';
            document.getElementById('disk-bar').style.width = d.disk_percent + '%';
        }}
        if (d.gpu_name) {{
            let shortGpu = d.gpu_name.replace('Intel(R)', 'Intel').replace('NVIDIA', '').trim();
            document.getElementById('gpu-val').innerText = shortGpu || d.gpu_name;
            document.getElementById('gpu-desc').innerText = 'Mức tải: ' + (d.gpu_percent || 0) + '%';
            document.getElementById('gpu-bar').style.width = Math.min(d.gpu_percent || 0, 100) + '%';
        }}
        document.getElementById('stock-val').innerText = d.stats.available_in_stock + ' cuốn';
        document.getElementById('sold-val').innerText = d.stats.sold_out + ' / ' + d.stats.pending_leads;
    }}).catch(() => {{}});
}}
let allCategories = [];
function fetchCategories() {{
    fetch('/api/categories').then(r => r.json()).then(cats => {{
        allCategories = cats || [];
        renderCategoryOptions();
    }}).catch(() => {{}});
}}
function renderCategoryOptions() {{
    let filterSel = document.getElementById('category-filter');
    let mSel = document.getElementById('m-category');
    let addSel = document.getElementById('add-category');
    let container = document.getElementById('cat-list-container');
    let curFilter = filterSel ? filterSel.value : '';
    let curM = mSel ? mSel.value : '';
    let curAdd = addSel ? addSel.value : '';
    if (filterSel) {{
        let fHtml = '<option value="">Tất cả thể loại</option>';
        allCategories.forEach(c => fHtml += `<option value="${{c}}">${{c}}</option>`);
        filterSel.innerHTML = fHtml; filterSel.value = curFilter;
    }}
    let optHtml = '<option value="">-- Chọn thể loại --</option>';
    allCategories.forEach(c => optHtml += `<option value="${{c}}">${{c}}</option>`);
    if (mSel) {{ mSel.innerHTML = optHtml; if (curM) mSel.value = curM; }}
    if (addSel) {{ addSel.innerHTML = optHtml; if (curAdd) addSel.value = curAdd; }}
    if (container) {{
        let cHtml = '';
        allCategories.forEach(c => cHtml += `<span class="cat-chip">${{c}} <span style="cursor:pointer; color:#f85149; font-weight:bold; margin-left:4px;" onclick="submitDeleteCategory('${{c}}')">&times;</span></span>`);
        container.innerHTML = cHtml || '<span style="color:#8b949e; font-size:12px;">Chưa có thể loại nào</span>';
    }}
}}
function openCatModal() {{
    document.getElementById('new-cat-name').value = '';
    document.getElementById('cat-modal').classList.add('open');
    renderCategoryOptions();
}}
function submitAddCategory() {{
    let name = document.getElementById('new-cat-name').value.trim();
    if (!name) {{ alert('Vui lòng nhập tên thể loại mới'); return; }}
    fetch('/api/add-category', {{
        method: 'POST', headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{ name: name }})
    }}).then(r => r.json()).then(res => {{
        if (res.success) {{
            document.getElementById('new-cat-name').value = '';
            allCategories = res.categories; renderCategoryOptions();
        }} else {{ alert('Không thể thêm: ' + (res.error || 'Đã tồn tại')); }}
    }});
}}
function submitDeleteCategory(name) {{
    if (!confirm('Xóa thể loại \"' + name + '\"? (Sách hiện có sẽ không bị ảnh hưởng)')) return;
    fetch('/api/delete-category', {{
        method: 'POST', headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{ name: name }})
    }}).then(r => r.json()).then(res => {{
        if (res.success) {{ allCategories = res.categories; renderCategoryOptions(); }}
    }});
}}
function fetchBooks() {{
    fetch('/api/books').then(r => r.json()).then(data => {{
        allBooks = data;
        renderTable();
    }}).catch(() => {{
        document.getElementById('books-tbody').innerHTML = '<tr><td colspan="8" style="text-align:center; color:#f85149;">Không thể tải dữ liệu sách.</td></tr>';
    }});
}}
function onPriceFilterChange() {{
    let val = document.getElementById('price-filter').value;
    let minInp = document.getElementById('min-price-input');
    let maxInp = document.getElementById('max-price-input');
    if (val === 'custom') {{
        minInp.style.display = 'inline-block';
        maxInp.style.display = 'inline-block';
    }} else {{
        minInp.style.display = 'none'; minInp.value = '';
        maxInp.style.display = 'none'; maxInp.value = '';
    }}
    renderTable();
}}
function resetFilters() {{
    ['search-input','category-filter','price-filter','min-price-input','max-price-input','status-filter'].forEach(id => document.getElementById(id).value = '');
    document.getElementById('min-price-input').style.display = 'none';
    document.getElementById('max-price-input').style.display = 'none';
    document.getElementById('sort-filter').value = 'id_desc';
    renderTable();
}}
function renderTable() {{
    let query = document.getElementById('search-input').value.toLowerCase().trim();
    let catFilter = document.getElementById('category-filter').value.trim();
    let statusFilter = document.getElementById('status-filter').value.trim();
    let priceVal = document.getElementById('price-filter').value;
    let sortVal = document.getElementById('sort-filter').value;
    let minP = NaN, maxP = NaN;
    if (priceVal === 'custom') {{
        minP = parseInt(document.getElementById('min-price-input').value);
        maxP = parseInt(document.getElementById('max-price-input').value);
    }} else if (priceVal && priceVal.includes('-')) {{
        let pts = priceVal.split('-');
        minP = parseInt(pts[0]);
        maxP = parseInt(pts[1]);
    }}
    let filtered = allBooks.filter(b => {{
        let qClean = query.replace(/^#/, '');
        let mQuery = !query || String(b.id) === qClean || String(b.id).includes(qClean) || (b.title && b.title.toLowerCase().includes(query)) || (b.author && b.author.toLowerCase().includes(query));
        let mCat = !catFilter || (b.category && b.category.trim() === catFilter);
        let mStatus = true;
        if (statusFilter === 'available') mStatus = b.status === 'available';
        else if (statusFilter === 'sold_out') mStatus = b.status === 'sold_out';
        else if (statusFilter === 'pending_review') mStatus = b.is_reviewed === 0;
        let pNum = b.price ? parseInt(String(b.price).replace(/[^0-9]/g, '')) : NaN;
        let mPrice = true;
        if (!isNaN(minP)) mPrice = mPrice && (!isNaN(pNum) && pNum >= minP);
        if (!isNaN(maxP)) mPrice = mPrice && (!isNaN(pNum) && pNum <= maxP);
        return mQuery && mCat && mStatus && mPrice;
    }});
    if (sortVal === 'id_asc') filtered.sort((a,b) => a.id - b.id);
    else if (sortVal === 'id_desc') filtered.sort((a,b) => b.id - a.id);
    else if (sortVal === 'price_asc') filtered.sort((a,b) => (parseInt(a.price)||0) - (parseInt(b.price)||0));
    else if (sortVal === 'price_desc') filtered.sort((a,b) => (parseInt(b.price)||0) - (parseInt(a.price)||0));
    else if (sortVal === 'title_asc') filtered.sort((a,b) => (a.title||'').localeCompare(b.title||'', 'vi'));
    let totalVal = filtered.reduce((acc, b) => acc + (parseInt(b.price) || 0), 0);
    let totalStr = totalVal > 0 ? ' | ' + totalVal.toLocaleString('vi-VN') + ' đ' : '';
    let displayList = filtered.slice(0, 100);
    let limitNote = filtered.length > 100 ? ' (tối đa 100 cuốn)' : '';
    document.getElementById('count-info').innerText = 'Hiển thị: ' + displayList.length + limitNote + ' / ' + allBooks.length + ' cuốn' + totalStr;
    if (!displayList.length) {{
        document.getElementById('books-tbody').innerHTML = '<tr><td colspan="8" style="text-align:center; padding: 20px; color:#8b949e;">Không tìm thấy sách nào phù hợp điều kiện lọc.</td></tr>';
        return;
    }}
    let html = '';
    displayList.forEach(b => {{
        let imgSrc = b.local_path ? '/storage/images/' + b.local_path.split('\\\\').pop().split('/').pop() : 'https://via.placeholder.com/44x60?text=No+Cover';
        let statusBadge = b.status === 'available' ? '<span class="badge badge-available">Còn hàng</span>' : '<span class="badge badge-sold">Đã bán</span>';
        let reviewBadge = b.is_reviewed === 1 ? '<span class="badge badge-approved">Đã soát</span>' : '<button class="btn btn-outline btn-sm" style="color:#3fb950; border-color:#238636; padding:2px 8px; font-size:11px;" onclick="approveBook(' + b.id + ')" title="Bấm để xác nhận đã soát cuốn này">✅ Duyệt</button>';
        let catBadge = b.category ? `<span class="badge-cat">${{b.category}}</span>` : '<span style="color:#8b949e">-</span>';
        html += `<tr>
            <td style="color:#8b949e;">#${{b.id}}</td>
            <td><img src="${{imgSrc}}" class="thumb" onclick="openEditModal(${{b.id}})" alt="Bìa" onerror="this.src='https://via.placeholder.com/44x60?text=No+Img'"></td>
            <td>
                <div style="font-weight:600; color:#f0f6fc;">${{b.title || 'Chưa rõ tựa sách'}}</div>
                <div style="font-size:12px; color:#8b949e;">${{b.author ? 'Tác giả: ' + b.author : 'Chưa rõ tác giả'}}</div>
            </td>
            <td>${{catBadge}}</td>
            <td style="font-weight:600; color:#3fb950;">${{formatPrice(b.price)}}</td>
            <td>${{statusBadge}}</td>
            <td>${{reviewBadge}}</td>
            <td style="text-align:center;"><button class="btn btn-outline btn-sm" onclick="openEditModal(${{b.id}})">✏️ Sửa / Soát</button></td>
        </tr>`;
    }});
    document.getElementById('books-tbody').innerHTML = html;
}}
function openEditModal(id) {{
    let b = allBooks.find(x => x.id === id);
    if (!b) return;
    document.getElementById('m-id').value = b.id;
    document.getElementById('m-title').value = b.title || '';
    document.getElementById('m-author').value = b.author || '';
    let catVal = (b.category || '').trim();
    let mSel = document.getElementById('m-category');
    if (catVal && !Array.from(mSel.options).some(o => o.value === catVal)) {{
        let opt = document.createElement('option');
        opt.value = catVal; opt.innerText = catVal; mSel.appendChild(opt);
    }}
    mSel.value = catVal;
    document.getElementById('m-price').value = b.price || '';
    document.getElementById('m-status').value = b.status || 'available';
    let imgSrc = b.local_path ? '/storage/images/' + b.local_path.split('\\\\').pop().split('/').pop() : 'https://via.placeholder.com/200x260?text=No+Cover';
    document.getElementById('m-preview').src = imgSrc;
    document.getElementById('edit-modal').classList.add('open');
}}
function saveBookEdit() {{
    let id = parseInt(document.getElementById('m-id').value);
    let title = document.getElementById('m-title').value.trim();
    let author = document.getElementById('m-author').value.trim();
    let category = document.getElementById('m-category').value.trim();
    let priceRaw = document.getElementById('m-price').value.trim();
    let status = document.getElementById('m-status').value;
    let price = parsePriceInput(priceRaw);
    if (!title) {{ alert('Vui lòng nhập tựa sách!'); return; }}
    fetch('/api/update-book', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{ id: id, title: title, author: author, category: category, price: price, status: status, is_single_book: 1, is_reviewed: 1 }})
    }}).then(r => r.json()).then(res => {{
        if (res.success) {{
            closeModal('edit-modal');
            fetchBooks();
            fetchMetrics();
        }} else {{ alert('Không thể lưu: ' + (res.error || 'Lỗi không xác định')); }}
    }});
}}
function submitAddBook() {{
    let status = document.getElementById('add-status').value;
    let category = document.getElementById('add-category').value.trim();
    let price = parsePriceInput(document.getElementById('add-price').value.trim());
    if (selectedFiles.length > 1) {{
        let btn = document.getElementById('add-submit-btn'); btn.disabled = true;
        let bInfo = document.getElementById('batch-info'), total = selectedFiles.length, done = 0;
        let addNext = function(idx) {{
            if (idx >= total) {{
                alert(`✅ Đã tải lên và nhận diện thành công ${{done}}/${{total}} cuốn sách vào kho!`);
                btn.disabled = false; closeModal('add-modal'); fetchBooks(); fetchMetrics(); return;
            }}
            bInfo.innerHTML = `⏳ <b>Đang tải & gọi AI nhận diện cuốn ${{idx+1}}/${{total}}...</b> Vui lòng chờ...`;
            let f = selectedFiles[idx], r = new FileReader();
            r.onload = function(e) {{
                fetch('/api/add-book', {{
                    method: 'POST', headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ auto_analyze: true, category: category, price: price, status: status, image_base64: e.target.result }})
                }}).then(res => res.json()).then(resData => {{ if (resData.success) done++; addNext(idx + 1); }}).catch(() => addNext(idx + 1));
            }};
            r.readAsDataURL(f);
        }};
        addNext(0); return;
    }}
    let title = document.getElementById('add-title').value.trim(), author = document.getElementById('add-author').value.trim();
    if (!title) {{ alert('Vui lòng nhập tựa sách!'); return; }}
    fetch('/api/add-book', {{
        method: 'POST', headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{ title: title, author: author, category: category, price: price, status: status, image_base64: addCoverBase64 }})
    }}).then(r => r.json()).then(res => {{
        if (res.success) {{ closeModal('add-modal'); fetchBooks(); fetchMetrics(); }} else {{ alert('Lỗi khi thêm: ' + (res.error || '')); }}
    }});
}}
function deleteCurrentBook() {{
    let id = parseInt(document.getElementById('m-id').value);
    if (!confirm('Bạn có chắc chắn muốn xóa vĩnh viễn cuốn sách này khỏi kho?')) return;
    fetch('/api/delete-book', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{ id: id }})
    }}).then(r => r.json()).then(res => {{
        if (res.success) {{
            closeModal('edit-modal');
            fetchBooks();
            fetchMetrics();
        }} else {{ alert('Lỗi khi xóa!'); }}
    }});
}}
function approveBook(id) {{
    fetch('/api/approve-book', {{ method: 'POST', headers: {{ 'Content-Type': 'application/json' }}, body: JSON.stringify({{ id: id }}) }}).then(r => r.json()).then(res => {{
        if (res.success) {{ let b = allBooks.find(x => x.id === id); if (b) b.is_reviewed = 1; renderTable(); fetchMetrics(); }}
    }});
}}
function quickApproveFromModal() {{
    let id = parseInt(document.getElementById('m-id').value);
    if (id) {{ approveBook(id); closeModal('edit-modal'); }}
}}
function approveAllPending() {{
    if (!confirm('Bạn muốn duyệt toàn bộ các cuốn sách đang chờ soát lại?')) return;
    fetch('/api/approve-all', {{ method: 'POST' }}).then(r => r.json()).then(res => {{
        if (res.success) {{ fetchBooks(); fetchMetrics(); }}
    }});
}}
let allLeads = [];
function fetchLeads() {{
    fetch('/api/leads').then(r => r.json()).then(data => {{
        allLeads = data || [];
        renderLeads();
    }}).catch(() => {{}});
}}
function renderLeads() {{
    let filter = document.getElementById('lead-status-filter') ? document.getElementById('lead-status-filter').value : '';
    let filtered = filter ? allLeads.filter(l => l.status === filter) : allLeads;
    let tbody = document.getElementById('leads-tbody');
    let info = document.getElementById('lead-count-info');
    if (info) info.innerText = 'Cơ hội: ' + filtered.length + ' bài viết';
    if (!filtered || filtered.length === 0) {{
        tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; padding: 25px; color:#8b949e;">Chưa có bài đăng khách hỏi mua nào phù hợp.</td></tr>';
        return;
    }}
    let html = '';
    filtered.forEach(l => {{
        let statusBadge = l.status === 'contacted' ? '<span class="badge badge-available">Đã liên hệ</span>' : '<span class="badge badge-pending">Chờ phản hồi</span>';
        let dateStr = l.created_at ? l.created_at.split('T')[0] : '';
        let postLink = l.post_url || l.group_url || '#';
        let priceStr = l.book_price ? Number(l.book_price).toLocaleString('vi-VN') + ' đ' : 'Chưa rõ giá';
        let nextStatus = l.status === 'contacted' ? 'pending' : 'contacted';
        let toggleText = l.status === 'contacted' ? '↩️ Đánh dấu chờ' : '✅ Đã liên hệ';
        html += `<tr>
            <td style="color:#8b949e; font-size:12px;">#${{l.id}}<br><span style="font-size:11px;">${{dateStr}}</span></td>
            <td>
                <div style="font-weight:600; color:#58a6ff;">${{l.matched_book_title || 'Sách trong kho'}}</div>
                <div style="font-size:12px; color:#3fb950; font-weight:600;">Giá kho: ${{priceStr}}</div>
            </td>
            <td><div style="max-width:380px; word-break:break-word; font-size:12px; color:#c9d1d9;">${{l.content_snippet || 'Không có mô tả'}}</div></td>
            <td>${{statusBadge}}</td>
            <td style="white-space:nowrap; text-align:center;">
                <a href="${{postLink}}" target="_blank" rel="noopener noreferrer" class="btn btn-outline btn-sm" style="text-decoration:none; display:inline-block;">🔗 Mở bài</a>
                <button class="btn btn-outline btn-sm" onclick="toggleLeadStatus(${{l.id}}, '${{nextStatus}}')">${{toggleText}}</button>
                <button class="btn btn-danger btn-sm" onclick="deleteLead(${{l.id}})">🗑️</button>
            </td>
        </tr>`;
    }});
    tbody.innerHTML = html;
}}
function toggleLeadStatus(id, newStatus) {{
    fetch('/api/update-lead', {{ method: 'POST', headers: {{ 'Content-Type': 'application/json' }}, body: JSON.stringify({{ id: id, status: newStatus }}) }}).then(r => r.json()).then(res => {{ if (res.success) {{ fetchLeads(); fetchMetrics(); }} }});
}}
function deleteLead(id) {{
    if (!confirm('Xóa cơ hội bán hàng này?')) return;
    fetch('/api/delete-lead', {{ method: 'POST', headers: {{ 'Content-Type': 'application/json' }}, body: JSON.stringify({{ id: id }}) }}).then(r => r.json()).then(res => {{ if (res.success) {{ fetchLeads(); fetchMetrics(); }} }});
}}
fetchMetrics();
fetchCategories();
fetchBooks();
fetchLeads();
setInterval(fetchMetrics, 10000);
</script>
</body>
</html>"""