def get_admin_scripts() -> str:
    return r"""let allBooks = [];
let currentPage = 1;
const PAGE_SIZE = 100;
function switchTab(tabId) {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    event.currentTarget.classList.add('active');
    document.getElementById(tabId).classList.add('active');
    if (tabId === 'tab-leads') fetchLeads();
}
function closeModal(id) { document.getElementById(id).classList.remove('open'); }
let addCoverBase64 = '', selectedFiles = [];
function openAddModal() {
    addCoverBase64 = ''; selectedFiles = [];
    ['add-title', 'add-author', 'add-price', 'add-cover-file'].forEach(id => { let el = document.getElementById(id); if (el) el.value = ''; });
    document.getElementById('add-category').value = '';
    document.getElementById('single-fields').style.display = 'block';
    let prev = document.getElementById('add-preview-img'); if (prev) { prev.src = ''; prev.style.display = 'none'; }
    let st = document.getElementById('add-ai-status'); if (st) { st.innerText = ''; st.style.display = 'none'; }
    let bi = document.getElementById('batch-info'); if (bi) bi.style.display = 'none';
    let btn = document.getElementById('add-submit-btn'); if (btn) { btn.innerText = '➕ Thêm Vào Kho'; btn.disabled = false; }
    document.getElementById('add-modal').classList.add('open');
}
function handleCoverUpload(event) {
    let files = event.target.files;
    if (!files || files.length === 0) return;
    selectedFiles = Array.from(files);
    let st = document.getElementById('add-ai-status'), prev = document.getElementById('add-preview-img'), sFields = document.getElementById('single-fields'), bInfo = document.getElementById('batch-info'), btn = document.getElementById('add-submit-btn');
    if (selectedFiles.length === 1) {
        sFields.style.display = 'block'; bInfo.style.display = 'none'; btn.innerText = '➕ Thêm Vào Kho';
        let reader = new FileReader();
        reader.onload = function(e) {
            addCoverBase64 = e.target.result;
            if (prev) { prev.src = addCoverBase64; prev.style.display = 'inline-block'; }
            if (st) { st.style.display = 'block'; st.style.color = '#58a6ff'; st.innerText = '⏳ Đang gọi Gemini AI đọc bìa sách...'; }
            fetch('/api/analyze-cover', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ image_base64: addCoverBase64 }) })
            .then(r => r.json()).then(res => {
                if (res.success) {
                    if (res.title) document.getElementById('add-title').value = res.title;
                    if (res.author) document.getElementById('add-author').value = res.author;
                    if (res.category) { let catSel = document.getElementById('add-category'); if (catSel && !Array.from(catSel.options).some(o => o.value === res.category)) { let opt = document.createElement('option'); opt.value = res.category; opt.innerText = res.category; catSel.appendChild(opt); } if (catSel) catSel.value = res.category; }
                    if (res.price) document.getElementById('add-price').value = res.price;
                    if (st) { st.style.color = '#3fb950'; st.innerText = '✅ AI đã nhận diện xong! Có thể sửa lại nếu cần.'; }
                } else { if (st) { st.style.color = '#d29922'; st.innerText = '⚠️ Không nhận diện rõ, vui lòng tự điền.'; } }
            }).catch(() => { if (st) { st.style.color = '#f85149'; st.innerText = '❌ Lỗi đọc ảnh, hãy tự điền thủ công.'; } });
        };
        reader.readAsDataURL(selectedFiles[0]);
    } else {
        sFields.style.display = 'none'; if (prev) prev.style.display = 'none'; if (st) st.style.display = 'none';
        bInfo.style.display = 'block';
        bInfo.innerHTML = `📸 <b>Đã chọn ${selectedFiles.length} ảnh bìa sách.</b><br><span style="color:#8b949e; font-size:12px;">Hệ thống sẽ nạp từng ảnh, gọi AI đọc tên/tác giả/thể loại/giá và thêm vào kho (trạng thái Chờ Soát để duyệt lại). Bạn có thể đặt giá hoặc thể loại chung bên dưới (hoặc để trống cho AI tự đọc).</span>`;
        btn.innerText = `🚀 Tải Lên & Nhận Diện Hàng Loạt (${selectedFiles.length} cuốn)`;
    }
}
function parsePriceInput(val) {
    if (!val) return "";
    let s = String(val).toLowerCase().replace(/[^0-9k]/g, '').trim();
    if (s.endsWith('k')) { let n = parseInt(s.slice(0, -1)); return isNaN(n) ? "" : String(n * 1000); }
    let n = parseInt(s);
    return isNaN(n) ? "" : (n < 1000 && n > 0 ? String(n * 1000) : String(n));
}
function formatPrice(price) {
    return (!price || isNaN(parseInt(price))) ? '<span style="color:#8b949e">Chưa có giá</span>' : Number(price).toLocaleString('vi-VN') + ' đ';
}
function setElText(id, txt) { let el = document.getElementById(id); if (el) el.innerText = txt; }
function setElWidth(id, pct) { let el = document.getElementById(id); if (el) el.style.width = pct + '%'; }
function fetchMetrics() {
    fetch('/api/metrics').then(r => r.json()).then(d => {
        setElText('ram-val', d.ram_used_gb + ' / ' + d.ram_total_gb + ' GB');
        setElText('ram-desc', 'Đang dùng: ' + d.ram_percent + '%');
        setElWidth('ram-bar', d.ram_percent);
        setElText('cpu-val', d.cpu_percent + ' %');
        setElWidth('cpu-bar', Math.min(d.cpu_percent, 100));
        if (d.disk_used_gb) {
            setElText('disk-val', d.disk_used_gb + ' / ' + d.disk_total_gb + ' GB');
            setElText('disk-desc', 'Trống: ' + d.disk_free_gb + ' GB (' + d.disk_percent + '%)');
            setElWidth('disk-bar', d.disk_percent);
        }
        if (d.gpu_name) {
            let shortGpu = String(d.gpu_name).replace('Intel(R)', 'Intel').replace('NVIDIA', '').trim();
            setElText('gpu-val', shortGpu || d.gpu_name);
            setElText('gpu-desc', 'Mức tải: ' + (d.gpu_percent || 0) + '%');
            setElWidth('gpu-bar', Math.min(d.gpu_percent || 0, 100));
        }
        if (d.stats) {
            setElText('stock-val', d.stats.available_in_stock + ' cuốn');
            setElText('sold-val', d.stats.sold_out + ' / ' + d.stats.pending_leads);
        }
        if (d.ai_status) {
            let ai = d.ai_status, aiEl = document.getElementById('ai-val');
            let stMap = {
                ok: ['✅ Hoạt động tốt', '#3fb950'],
                quota_exceeded: ['🚨 Hết hạn mức (429)', '#f85149'],
                auth_error: ['🔑 Lỗi API Key', '#f85149'],
                unconfigured: ['⚪ Chưa gắn API Key', '#8b949e'],
                error: ['⚠️ Lỗi kết nối AI', '#d29922']
            };
            let [lbl, clr] = stMap[ai.status] || ['✅ Sẵn sàng', '#3fb950'];
            if (aiEl) { aiEl.innerText = lbl; aiEl.style.color = clr; }
            let tok = Number(ai.total_tokens_today || 0).toLocaleString('vi-VN');
            let desc = `Hôm nay: ${tok} token (${ai.requests_today || 0} lượt)`;
            if (ai.status === 'quota_exceeded' || ai.status === 'auth_error') desc += ai.last_error_at ? ` • Lỗi lúc ${ai.last_error_at}` : '';
            setElText('ai-desc', desc);
        }
    }).catch(() => {});
}
let allCategories = [];
function fetchCategories() {
    fetch('/api/categories').then(r => r.json()).then(cats => {
        allCategories = cats || [];
        renderCategoryOptions();
    }).catch(() => {});
}
function normCat(s) { return String(s || '').normalize('NFC').replace(/\s+/g, ' ').trim().toLowerCase(); }
function renderCategoryOptions() {
    let filterSel = document.getElementById('category-filter'), mSel = document.getElementById('m-category'), addSel = document.getElementById('add-category'), container = document.getElementById('cat-list-container');
    let curFilter = filterSel ? filterSel.value : '', curM = mSel ? mSel.value : '', curAdd = addSel ? addSel.value : '';
    let mergedMap = new Map();
    allCategories.forEach(c => { let k = normCat(c); if (k && !mergedMap.has(k)) mergedMap.set(k, c.trim()); });
    allBooks.forEach(b => { let raw = (b.category || '').replace(/\s+/g, ' ').trim(); let k = normCat(raw); if (k && !mergedMap.has(k)) mergedMap.set(k, raw); });
    let filterCats = Array.from(mergedMap.values()).sort((a, b) => a.localeCompare(b, 'vi'));
    if (filterSel) {
        let fHtml = '<option value="">Tất cả thể loại</option>';
        filterCats.forEach(c => fHtml += `<option value="${c}">${c}</option>`);
        filterSel.innerHTML = fHtml; filterSel.value = curFilter;
    }
    let optHtml = '<option value="">-- Chọn thể loại --</option>';
    allCategories.forEach(c => optHtml += `<option value="${c}">${c}</option>`);
    if (mSel) { mSel.innerHTML = optHtml; if (curM) mSel.value = curM; }
    if (addSel) { addSel.innerHTML = optHtml; if (curAdd) addSel.value = curAdd; }
    if (container) {
        let cHtml = '';
        allCategories.forEach(c => cHtml += `<span class="cat-chip">${c} <span style="cursor:pointer; color:#f85149; font-weight:bold; margin-left:4px;" onclick="submitDeleteCategory('${c}')">&times;</span></span>`);
        container.innerHTML = cHtml || '<span style="color:#8b949e; font-size:12px;">Chưa có thể loại nào</span>';
    }
}
function openCatModal() {
    document.getElementById('new-cat-name').value = '';
    document.getElementById('cat-modal').classList.add('open');
    renderCategoryOptions();
}
function submitAddCategory() {
    let name = document.getElementById('new-cat-name').value.trim();
    if (!name) { alert('Vui lòng nhập tên thể loại mới'); return; }
    fetch('/api/add-category', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: name })
    }).then(r => r.json()).then(res => {
        if (res.success) {
            document.getElementById('new-cat-name').value = '';
            allCategories = res.categories; renderCategoryOptions();
        } else { alert('Không thể thêm: ' + (res.error || 'Đã tồn tại')); }
    });
}
function submitDeleteCategory(name) {
    if (!confirm('Xóa thể loại "' + name + '"? (Sách hiện có sẽ không bị ảnh hưởng)')) return;
    fetch('/api/delete-category', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: name })
    }).then(r => r.json()).then(res => {
        if (res.success) { allCategories = res.categories; renderCategoryOptions(); }
    });
}
function fetchBooks() {
    fetch('/api/books').then(r => r.json()).then(data => {
        allBooks = data;
        renderCategoryOptions();
        renderTable(false);
    }).catch(() => {
        document.getElementById('books-tbody').innerHTML = '<tr><td colspan="8" style="text-align:center; color:#f85149;">Không thể tải dữ liệu sách.</td></tr>';
    });
}
function onCustomPriceInput(el) {
    let v = el.value.replace(/[^0-9kK]/g, '');
    let fmt = (v.length >= 4 && !/k/i.test(v)) ? parseInt(v, 10).toLocaleString('vi-VN') : v;
    if (el.value !== fmt) el.value = fmt;
    renderTable(true);
}
function onPriceFilterChange() {
    let isCustom = document.getElementById('price-filter').value === 'custom';
    document.getElementById('custom-price-box').style.display = isCustom ? 'inline-flex' : 'none';
    if (!isCustom) { document.getElementById('min-price-input').value = ''; document.getElementById('max-price-input').value = ''; }
    renderTable(true);
}
function resetFilters() {
    ['search-input','category-filter','price-filter','min-price-input','max-price-input','status-filter'].forEach(id => document.getElementById(id).value = '');
    document.getElementById('custom-price-box').style.display = 'none';
    document.getElementById('sort-filter').value = 'id_desc';
    renderTable(true);
}
function goToPage(p) {
    currentPage = p;
    renderTable(false);
    let el = document.getElementById('tab-books');
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
}
function renderPagination(totalPages, totalFiltered) {
    let bar = document.getElementById('pagination-bar');
    if (!bar) return;
    if (totalFiltered <= PAGE_SIZE) { bar.innerHTML = ''; return; }
    let items = [], pages = new Set([1, totalPages]);
    for (let i = Math.max(1, currentPage - 2); i <= Math.min(totalPages, currentPage + 2); i++) pages.add(i);
    let sorted = Array.from(pages).sort((a, b) => a - b);
    let html = `<button class="page-btn" ${currentPage <= 1 ? 'disabled' : `onclick="goToPage(${currentPage - 1})"`}>« Trước</button>`;
    let prev = 0;
    sorted.forEach(p => {
        if (prev && p - prev > 1) html += '<span class="page-ellipsis">...</span>';
        html += `<button class="page-btn ${p === currentPage ? 'active' : ''}" onclick="goToPage(${p})">${p}</button>`;
        prev = p;
    });
    html += `<button class="page-btn" ${currentPage >= totalPages ? 'disabled' : `onclick="goToPage(${currentPage + 1})"`}>Sau »</button>`;
    html += `<span class="page-info">Trang ${currentPage} / ${totalPages}</span>`;
    bar.innerHTML = html;
}
function renderTable(resetPage = false) {
    if (resetPage) currentPage = 1;
    let query = document.getElementById('search-input').value.toLowerCase().trim();
    let catFilter = normCat(document.getElementById('category-filter').value);
    let statusFilter = document.getElementById('status-filter').value.trim();
    let priceVal = document.getElementById('price-filter').value;
    let sortVal = document.getElementById('sort-filter').value;
    let minP = NaN, maxP = NaN;
    if (priceVal === 'custom') {
        minP = parseInt(parsePriceInput(document.getElementById('min-price-input').value));
        maxP = parseInt(parsePriceInput(document.getElementById('max-price-input').value));
    } else if (priceVal && priceVal.includes('-')) {
        let pts = priceVal.split('-');
        minP = parseInt(pts[0]);
        maxP = parseInt(pts[1]);
    }
    let filtered = allBooks.filter(b => {
        let qClean = query.replace(/^#/, '');
        let mQuery = !query || String(b.id) === qClean || String(b.id).includes(qClean) || (b.title && b.title.toLowerCase().includes(query)) || (b.author && b.author.toLowerCase().includes(query));
        let mCat = !catFilter || (b.category && normCat(b.category) === catFilter);
        let mStatus = true;
        if (statusFilter === 'available') mStatus = b.status === 'available';
        else if (statusFilter === 'sold_out') mStatus = b.status === 'sold_out';
        else if (statusFilter === 'pending_review') mStatus = b.is_reviewed === 0;
        let pNum = b.price ? parseInt(String(b.price).replace(/[^0-9]/g, '')) : NaN;
        let mPrice = priceVal === 'no_price' ? (isNaN(pNum) || pNum <= 0) : true;
        if (!isNaN(minP)) mPrice = mPrice && (!isNaN(pNum) && pNum >= minP);
        if (!isNaN(maxP)) mPrice = mPrice && (!isNaN(pNum) && pNum <= maxP);
        return mQuery && mCat && mStatus && mPrice;
    });
    if (sortVal === 'id_asc') filtered.sort((a,b) => a.id - b.id);
    else if (sortVal === 'id_desc') filtered.sort((a,b) => b.id - a.id);
    else if (sortVal === 'price_asc') filtered.sort((a,b) => (parseInt(a.price)||0) - (parseInt(b.price)||0));
    else if (sortVal === 'price_desc') filtered.sort((a,b) => (parseInt(b.price)||0) - (parseInt(a.price)||0));
    else if (sortVal === 'title_asc') filtered.sort((a,b) => (a.title||'').localeCompare(b.title||'', 'vi'));
    let totalVal = filtered.reduce((acc, b) => acc + (parseInt(b.price) || 0), 0);
    let totalStr = totalVal > 0 ? ' | ' + totalVal.toLocaleString('vi-VN') + ' đ' : '';
    let totalFiltered = filtered.length;
    let totalPages = Math.max(1, Math.ceil(totalFiltered / PAGE_SIZE));
    if (currentPage > totalPages) currentPage = totalPages;
    if (currentPage < 1) currentPage = 1;
    let startIdx = (currentPage - 1) * PAGE_SIZE;
    let displayList = filtered.slice(startIdx, startIdx + PAGE_SIZE);
    document.getElementById('count-info').innerText = totalFiltered === 0
        ? 'Hiển thị: 0 / ' + allBooks.length + ' cuốn'
        : `Hiển thị: ${startIdx + 1}–${startIdx + displayList.length} / ${totalFiltered} cuốn` + (totalFiltered !== allBooks.length ? ` (Tổng kho: ${allBooks.length})` : '') + totalStr;
    renderPagination(totalPages, totalFiltered);
    if (!displayList.length) {
        document.getElementById('books-tbody').innerHTML = '<tr><td colspan="8" style="text-align:center; padding: 20px; color:#8b949e;">Không tìm thấy sách nào phù hợp điều kiện lọc.</td></tr>';
        return;
    }
    let html = '';
    displayList.forEach(b => {
        let imgSrc = b.local_path ? '/storage/images/' + b.local_path.split('\\').pop().split('/').pop() : 'https://via.placeholder.com/44x60?text=No+Cover';
        let statusBadge = b.status === 'available' ? '<span class="badge badge-available">Còn hàng</span>' : '<span class="badge badge-sold">Đã bán</span>';
        let reviewBadge = b.is_reviewed === 1 ? '<span class="badge badge-approved">Đã soát</span>' : '<button class="btn btn-outline btn-sm" style="color:#3fb950; border-color:#238636; padding:2px 8px; font-size:11px;" onclick="approveBook(' + b.id + ')" title="Bấm để xác nhận đã soát cuốn này">✅ Duyệt</button>';
        let catBadge = b.category ? `<span class="badge-cat">${b.category}</span>` : '<span style="color:#8b949e">-</span>';
        html += `<tr>
            <td style="color:#8b949e;">#${b.id}</td>
            <td><img src="${imgSrc}" class="thumb" onclick="openEditModal(${b.id})" alt="Bìa" onerror="this.src='https://via.placeholder.com/44x60?text=No+Img'"></td>
            <td>
                <div style="font-weight:600; color:#f0f6fc;">${b.title || 'Chưa rõ tựa sách'}</div>
                <div style="font-size:12px; color:#8b949e;">${b.author ? 'Tác giả: ' + b.author : 'Chưa rõ tác giả'}</div>
            </td>
            <td>${catBadge}</td>
            <td style="font-weight:600; color:#3fb950;">${formatPrice(b.price)}</td>
            <td>${statusBadge}</td>
            <td>${reviewBadge}</td>
            <td style="text-align:center;"><button class="btn btn-outline btn-sm" onclick="openEditModal(${b.id})">✏️ Sửa / Soát</button></td>
        </tr>`;
    });
    document.getElementById('books-tbody').innerHTML = html;
}
function openEditModal(id) {
    let b = allBooks.find(x => x.id === id);
    if (!b) return;
    document.getElementById('m-id').value = b.id;
    document.getElementById('m-title').value = b.title || '';
    document.getElementById('m-author').value = b.author || '';
    let catVal = (b.category || '').trim();
    let mSel = document.getElementById('m-category');
    if (catVal && !Array.from(mSel.options).some(o => o.value === catVal)) {
        let opt = document.createElement('option');
        opt.value = catVal; opt.innerText = catVal; mSel.appendChild(opt);
    }
    mSel.value = catVal;
    document.getElementById('m-price').value = b.price || '';
    document.getElementById('m-status').value = b.status || 'available';
    let imgSrc = b.local_path ? '/storage/images/' + b.local_path.split('\\').pop().split('/').pop() : 'https://via.placeholder.com/200x260?text=No+Cover';
    document.getElementById('m-preview').src = imgSrc;
    document.getElementById('edit-modal').classList.add('open');
}
function saveBookEdit() {
    let id = parseInt(document.getElementById('m-id').value);
    let title = document.getElementById('m-title').value.trim();
    let author = document.getElementById('m-author').value.trim();
    let category = document.getElementById('m-category').value.trim();
    let priceRaw = document.getElementById('m-price').value.trim();
    let status = document.getElementById('m-status').value;
    let price = parsePriceInput(priceRaw);
    if (!title) { alert('Vui lòng nhập tựa sách!'); return; }
    fetch('/api/update-book', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: id, title: title, author: author, category: category, price: price, status: status, is_single_book: 1, is_reviewed: 1 })
    }).then(r => r.json()).then(res => {
        if (res.success) {
            closeModal('edit-modal');
            fetchBooks();
            fetchMetrics();
        } else { alert('Không thể lưu: ' + (res.error || 'Lỗi không xác định')); }
    });
}
function submitAddBook() {
    let status = document.getElementById('add-status').value;
    let category = document.getElementById('add-category').value.trim();
    let price = parsePriceInput(document.getElementById('add-price').value.trim());
    if (selectedFiles.length > 1) {
        let btn = document.getElementById('add-submit-btn'); btn.disabled = true;
        let bInfo = document.getElementById('batch-info'), total = selectedFiles.length, done = 0;
        let addNext = function(idx) {
            if (idx >= total) {
                alert(`✅ Đã tải lên và nhận diện thành công ${done}/${total} cuốn sách vào kho!`);
                btn.disabled = false; closeModal('add-modal'); fetchBooks(); fetchMetrics(); return;
            }
            bInfo.innerHTML = `⏳ <b>Đang tải & gọi AI nhận diện cuốn ${idx+1}/${total}...</b> Vui lòng chờ...`;
            let f = selectedFiles[idx], r = new FileReader();
            r.onload = function(e) {
                fetch('/api/add-book', {
                    method: 'POST', headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ auto_analyze: true, category: category, price: price, status: status, image_base64: e.target.result })
                }).then(res => res.json()).then(resData => { if (resData.success) done++; addNext(idx + 1); }).catch(() => addNext(idx + 1));
            };
            r.readAsDataURL(f);
        };
        addNext(0); return;
    }
    let title = document.getElementById('add-title').value.trim(), author = document.getElementById('add-author').value.trim();
    if (!title) { alert('Vui lòng nhập tựa sách!'); return; }
    fetch('/api/add-book', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: title, author: author, category: category, price: price, status: status, image_base64: addCoverBase64 })
    }).then(r => r.json()).then(res => {
        if (res.success) { closeModal('add-modal'); fetchBooks(); fetchMetrics(); } else { alert('Lỗi khi thêm: ' + (res.error || '')); }
    });
}
function deleteCurrentBook() {
    let id = parseInt(document.getElementById('m-id').value);
    if (!confirm('Bạn có chắc chắn muốn xóa vĩnh viễn cuốn sách này khỏi kho?')) return;
    fetch('/api/delete-book', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: id })
    }).then(r => r.json()).then(res => {
        if (res.success) {
            closeModal('edit-modal');
            fetchBooks();
            fetchMetrics();
        } else { alert('Lỗi khi xóa!'); }
    });
}
function approveBook(id) {
    fetch('/api/approve-book', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ id: id }) }).then(r => r.json()).then(res => {
        if (res.success) { let b = allBooks.find(x => x.id === id); if (b) b.is_reviewed = 1; renderTable(false); fetchMetrics(); }
    });
}
function quickApproveFromModal() {
    let id = parseInt(document.getElementById('m-id').value);
    if (id) { approveBook(id); closeModal('edit-modal'); }
}
function approveAllPending() {
    if (!confirm('Bạn muốn duyệt toàn bộ các cuốn sách đang chờ soát lại?')) return;
    fetch('/api/approve-all', { method: 'POST' }).then(r => r.json()).then(res => {
        if (res.success) { fetchBooks(); fetchMetrics(); }
    });
}
let allLeads = [];
function fetchLeads() {
    fetch('/api/leads').then(r => r.json()).then(data => {
        allLeads = data || [];
        renderLeads();
    }).catch(() => {});
}
function renderLeads() {
    let filter = document.getElementById('lead-status-filter') ? document.getElementById('lead-status-filter').value : '';
    let filtered = filter ? allLeads.filter(l => l.status === filter) : allLeads;
    let tbody = document.getElementById('leads-tbody');
    let info = document.getElementById('lead-count-info');
    if (info) info.innerText = 'Cơ hội: ' + filtered.length + ' bài viết';
    if (!filtered || filtered.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; padding: 25px; color:#8b949e;">Chưa có bài đăng khách hỏi mua nào phù hợp.</td></tr>';
        return;
    }
    let html = '';
    filtered.forEach(l => {
        let statusBadge = l.status === 'contacted' ? '<span class="badge badge-available">Đã liên hệ</span>' : '<span class="badge badge-pending">Chờ phản hồi</span>';
        let dateStr = l.created_at ? l.created_at.split('T')[0] : '';
        let postLink = l.post_url || l.group_url || '#';
        let priceStr = l.book_price ? Number(l.book_price).toLocaleString('vi-VN') + ' đ' : 'Chưa rõ giá';
        let nextStatus = l.status === 'contacted' ? 'pending' : 'contacted';
        let toggleText = l.status === 'contacted' ? '↩️ Đánh dấu chờ' : '✅ Đã liên hệ';
        html += `<tr>
            <td style="color:#8b949e; font-size:12px;">#${l.id}<br><span style="font-size:11px;">${dateStr}</span></td>
            <td>
                <div style="font-weight:600; color:#58a6ff;">${l.matched_book_title || 'Sách trong kho'}</div>
                <div style="font-size:12px; color:#3fb950; font-weight:600;">Giá kho: ${priceStr}</div>
            </td>
            <td><div style="max-width:380px; word-break:break-word; font-size:12px; color:#c9d1d9;">${l.content_snippet || 'Không có mô tả'}</div></td>
            <td>${statusBadge}</td>
            <td style="white-space:nowrap; text-align:center;">
                <a href="${postLink}" target="_blank" rel="noopener noreferrer" class="btn btn-outline btn-sm" style="text-decoration:none; display:inline-block;">🔗 Mở bài</a>
                <button class="btn btn-outline btn-sm" onclick="toggleLeadStatus(${l.id}, '${nextStatus}')">${toggleText}</button>
                <button class="btn btn-danger btn-sm" onclick="deleteLead(${l.id})">🗑️</button>
            </td>
        </tr>`;
    });
    tbody.innerHTML = html;
}
function toggleLeadStatus(id, newStatus) {
    fetch('/api/update-lead', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ id: id, status: newStatus }) }).then(r => r.json()).then(res => { if (res.success) { fetchLeads(); fetchMetrics(); } });
}
function deleteLead(id) {
    if (!confirm('Xóa cơ hội bán hàng này?')) return;
    fetch('/api/delete-lead', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ id: id }) }).then(r => r.json()).then(res => { if (res.success) { fetchLeads(); fetchMetrics(); } });
}
fetchMetrics();
fetchCategories();
fetchBooks();
fetchLeads();
setInterval(fetchMetrics, 10000);"""
