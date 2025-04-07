/**
 * 成績管理系統 - 成績表格腳本
 * 
 * 負責處理成績表格的互動功能：
 * - 初始化數據表格
 * - 成績儲存格編輯
 * - AJAX 更新到伺服器
 * - 班級、學生和成績項目管理
 */

document.addEventListener('DOMContentLoaded', function() {
    // 初始化數據表格
    const gradesTable = document.getElementById('gradesTable');
    if (gradesTable) {
        const tableInstance = new DataTable('#gradesTable', {
            responsive: true,
            paging: true,
            ordering: true,
            info: true,
            lengthMenu: [10, 25, 50, 100],
            language: {
                search: "搜尋學生：",
                lengthMenu: "每頁顯示 _MENU_ 名學生",
                info: "顯示第 _START_ 至 _END_ 名學生，共 _TOTAL_ 名",
                emptyTable: "此班級中沒有找到學生",
                paginate: {
                    first: "首頁",
                    last: "末頁",
                    next: "下一頁",
                    previous: "上一頁"
                }
            },
            columnDefs: [
                { orderable: false, targets: -1 } // 禁止對操作列進行排序
            ]
        });

        // 為樣式添加 DataTables 包裝器類
        document.querySelector('.dataTables_wrapper').classList.add('mt-3');
    }

    // 初始化學生表格
    const studentsTable = document.getElementById('studentsTable');
    if (studentsTable) {
        const tableInstance = new DataTable('#studentsTable', {
            responsive: true,
            paging: true,
            ordering: true,
            info: true,
            lengthMenu: [10, 25, 50, 100],
            language: {
                search: "搜尋學生：",
                lengthMenu: "每頁顯示 _MENU_ 名學生",
                info: "顯示第 _START_ 至 _END_ 名學生，共 _TOTAL_ 名",
                emptyTable: "此班級中沒有找到學生",
                paginate: {
                    first: "首頁",
                    last: "末頁",
                    next: "下一頁",
                    previous: "上一頁"
                }
            }
        });
    }

    // 設置成績編輯功能
    setupGradeEditing();

    // 設置學期選擇器
    const semesterSelector = document.getElementById('semesterSelector');
    if (semesterSelector) {
        semesterSelector.addEventListener('change', function() {
            const semester = this.value;
            window.location.href = `/teacher/grades?semester=${semester}`;
        });
    }

    // 設置班級選擇器
    const classSelector = document.getElementById('classSelector');
    if (classSelector) {
        classSelector.addEventListener('change', function() {
            const classId = this.value;
            const semester = semesterSelector ? semesterSelector.value : '';
            if (classId) {
                window.location.href = `/teacher/grades?semester=${semester}&class_id=${classId}`;
            }
        });
    }

    // 設置模態框按鈕事件
    setupModalEvents();
});

/**
 * 設置模態框相關事件
 */
function setupModalEvents() {
    // 添加學期按鈕
    const saveNewSemesterBtn = document.getElementById('saveNewSemester');
    if (saveNewSemesterBtn) {
        saveNewSemesterBtn.addEventListener('click', function() {
            const newSemesterInput = document.getElementById('newSemester');
            const semester = newSemesterInput.value.trim();
            
            if (!semester) {
                alert('請輸入學期');
                return;
            }
            
            fetch('/api/semesters', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ semester })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // 關閉模態框
                    const modal = bootstrap.Modal.getInstance(document.getElementById('addSemesterModal'));
                    modal.hide();
                    
                    // 刷新學期選擇器
                    const semesterSelector = document.getElementById('semesterSelector');
                    if (semesterSelector) {
                        // 清空現有選項
                        semesterSelector.innerHTML = '';
                        
                        // 添加新選項
                        data.semesters.forEach(sem => {
                            const option = document.createElement('option');
                            option.value = sem;
                            option.textContent = sem;
                            option.selected = sem === semester;
                            semesterSelector.appendChild(option);
                        });
                    }
                    
                    alert('學期添加成功');
                } else {
                    alert(data.message || '學期添加失敗');
                }
            })
            .catch(error => {
                console.error('Error adding semester:', error);
                alert('學期添加失敗');
            });
        });
    }
    
    // 添加班級按鈕
    const saveNewClassBtn = document.getElementById('saveNewClass');
    if (saveNewClassBtn) {
        saveNewClassBtn.addEventListener('click', function() {
            const newClassNameInput = document.getElementById('newClassName');
            const newClassSemesterSelect = document.getElementById('newClassSemester');
            
            const name = newClassNameInput.value.trim();
            const semester = newClassSemesterSelect.value;
            
            if (!name) {
                alert('請輸入班級名稱');
                return;
            }
            
            fetch('/api/classes', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ name, semester })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // 關閉模態框
                    const modal = bootstrap.Modal.getInstance(document.getElementById('addClassModal'));
                    modal.hide();
                    
                    // 刷新頁面
                    window.location.href = `/teacher/grades?semester=${semester}&class_id=${data.class.id}`;
                } else {
                    alert(data.message || '班級創建失敗');
                }
            })
            .catch(error => {
                console.error('Error creating class:', error);
                alert('班級創建失敗');
            });
        });
    }
    
    // 儲存班級資訊按鈕
    const saveClassInfoBtn = document.getElementById('saveClassInfo');
    if (saveClassInfoBtn) {
        saveClassInfoBtn.addEventListener('click', function() {
            const classNameInput = document.getElementById('className');
            const className = classNameInput.value.trim();
            
            if (!className) {
                alert('請輸入班級名稱');
                return;
            }
            
            // 獲取當前班級ID
            const classSelector = document.getElementById('classSelector');
            const classId = classSelector.value;
            
            if (!classId) {
                alert('請先選擇班級');
                return;
            }
            
            fetch(`/api/classes/${classId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ name: className })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('班級更新成功');
                    
                    // 更新班級選擇器中的名稱
                    const option = classSelector.querySelector(`option[value="${classId}"]`);
                    if (option) {
                        option.textContent = className;
                    }
                } else {
                    alert(data.message || '班級更新失敗');
                }
            })
            .catch(error => {
                console.error('Error updating class:', error);
                alert('班級更新失敗');
            });
        });
    }
    
    // 添加學生按鈕
    const addStudentBtn = document.getElementById('addStudentBtn');
    if (addStudentBtn) {
        addStudentBtn.addEventListener('click', function() {
            // 清空學生表單
            document.getElementById('studentForm').reset();
            document.getElementById('studentId').value = '';
            
            // 打開學生編輯模態框
            const studentModal = new bootstrap.Modal(document.getElementById('studentModal'));
            studentModal.show();
        });
    }
    
    // 儲存學生按鈕
    const saveStudentBtn = document.getElementById('saveStudent');
    if (saveStudentBtn) {
        saveStudentBtn.addEventListener('click', function() {
            const studentIdInput = document.getElementById('studentId');
            const seatNumberInput = document.getElementById('seatNumber');
            const studentNameInput = document.getElementById('studentName');
            const studentIdValueInput = document.getElementById('studentIdInput');
            
            const studentId = studentIdInput.value;
            const seatNumber = seatNumberInput.value.trim();
            const name = studentNameInput.value.trim();
            const studentIdValue = studentIdValueInput.value.trim();
            
            if (!name) {
                alert('請輸入學生姓名');
                return;
            }
            
            if (!seatNumber) {
                alert('請輸入座號');
                return;
            }
            
            // 獲取當前班級ID
            const classSelector = document.getElementById('classSelector');
            const classId = classSelector.value;
            
            if (!classId) {
                alert('請先選擇班級');
                return;
            }
            
            // 如果是更新現有學生
            if (studentId) {
                fetch(`/api/students/${studentId}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        name,
                        seat_number: seatNumber,
                        student_id: studentIdValue
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // 關閉模態框
                        const modal = bootstrap.Modal.getInstance(document.getElementById('studentModal'));
                        modal.hide();
                        
                        // 刷新頁面以顯示更新的學生
                        window.location.reload();
                    } else {
                        alert(data.message || '學生更新失敗');
                    }
                })
                .catch(error => {
                    console.error('Error updating student:', error);
                    alert('學生更新失敗');
                });
            } else {
                // 創建新學生
                fetch(`/api/classes/${classId}/students`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        name,
                        seat_number: seatNumber,
                        student_id: studentIdValue
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // 關閉模態框
                        const modal = bootstrap.Modal.getInstance(document.getElementById('studentModal'));
                        modal.hide();
                        
                        // 刷新頁面以顯示新學生
                        window.location.reload();
                    } else {
                        alert(data.message || '學生創建失敗');
                    }
                })
                .catch(error => {
                    console.error('Error creating student:', error);
                    alert('學生創建失敗');
                });
            }
        });
    }
    
    // 編輯和刪除學生按鈕
    const editStudentBtns = document.querySelectorAll('.edit-student');
    const deleteStudentBtns = document.querySelectorAll('.delete-student');
    
    editStudentBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const studentId = this.getAttribute('data-student-id');
            if (!studentId) return;
            
            // 獲取當前班級ID
            const classId = document.getElementById('classSelector').value;
            
            // 獲取學生數據
            fetch(`/api/classes/${classId}/students`)
            .then(response => response.json())
            .then(data => {
                const student = data.students.find(s => s.id == studentId);
                if (student) {
                    // 填充表單
                    document.getElementById('studentId').value = student.id;
                    document.getElementById('seatNumber').value = student.seat_number;
                    document.getElementById('studentName').value = student.name;
                    document.getElementById('studentIdInput').value = student.student_id;
                    
                    // 打開模態框
                    const studentModal = new bootstrap.Modal(document.getElementById('studentModal'));
                    studentModal.show();
                }
            })
            .catch(error => {
                console.error('Error fetching student data:', error);
                alert('無法獲取學生數據');
            });
        });
    });
    
    deleteStudentBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const studentId = this.getAttribute('data-student-id');
            if (!studentId) return;
            
            if (confirm('確定要刪除這個學生嗎？此操作不可恢復。')) {
                fetch(`/api/students/${studentId}`, {
                    method: 'DELETE'
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // 刷新頁面
                        window.location.reload();
                    } else {
                        alert(data.message || '學生刪除失敗');
                    }
                })
                .catch(error => {
                    console.error('Error deleting student:', error);
                    alert('學生刪除失敗');
                });
            }
        });
    });
    
    // 成績項目相關按鈕
    const saveGradeItemBtn = document.getElementById('saveGradeItem');
    if (saveGradeItemBtn) {
        saveGradeItemBtn.addEventListener('click', function() {
            const gradeItemNameInput = document.getElementById('gradeItemName');
            const gradeItemMaxScoreInput = document.getElementById('gradeItemMaxScore');
            
            const name = gradeItemNameInput.value.trim();
            const maxScore = gradeItemMaxScoreInput.value.trim();
            
            if (!name) {
                alert('請輸入成績項目名稱');
                return;
            }
            
            if (!maxScore) {
                alert('請輸入最高分數');
                return;
            }
            
            // 獲取當前班級ID
            const classId = document.getElementById('classSelector').value;
            
            if (!classId) {
                alert('請先選擇班級');
                return;
            }
            
            fetch(`/api/classes/${classId}/grade_items`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    name,
                    max_score: maxScore
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // 關閉模態框
                    const modal = bootstrap.Modal.getInstance(document.getElementById('addGradeItemModal'));
                    modal.hide();
                    
                    // 刷新頁面以顯示新成績項目
                    window.location.reload();
                } else {
                    alert(data.message || '成績項目創建失敗');
                }
            })
            .catch(error => {
                console.error('Error creating grade item:', error);
                alert('成績項目創建失敗');
            });
        });
    }
}

/**
 * 設置成績編輯功能
 */
function setupGradeEditing() {
    // 設置刪除成績項目按鈕
    const deleteGradeItemBtns = document.querySelectorAll('.delete-grade-item');
    deleteGradeItemBtns.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            const gradeItemId = this.getAttribute('data-grade-item-id');
            if (!gradeItemId) return;
            
            if (confirm('確定要刪除這個成績項目嗎？此操作會刪除所有相關成績數據且不可恢復。')) {
                fetch(`/api/grade_items/${gradeItemId}`, {
                    method: 'DELETE'
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // 刷新頁面
                        window.location.reload();
                    } else {
                        alert(data.message || '成績項目刪除失敗');
                    }
                })
                .catch(error => {
                    console.error('Error deleting grade item:', error);
                    alert('成績項目刪除失敗');
                });
            }
        });
    });

    const gradeCells = document.querySelectorAll('.grade-cell');
    
    gradeCells.forEach(cell => {
        const input = cell.querySelector('input');
        const studentId = cell.getAttribute('data-student-id');
        const gradeItemId = cell.getAttribute('data-grade-item-id');
        
        if (input) {
            // 保存初始值以便比較
            let originalValue = input.value;
            
            // 焦點離開時儲存
            input.addEventListener('blur', function() {
                if (this.value !== originalValue) {
                    saveGrade(studentId, gradeItemId, this.value, cell);
                    originalValue = this.value;
                }
            });
            
            // 按Enter鍵儲存並移至下一個輸入框
            input.addEventListener('keydown', function(e) {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    if (this.value !== originalValue) {
                        saveGrade(studentId, gradeItemId, this.value, cell);
                        originalValue = this.value;
                    }
                    // 移至下一個輸入框
                    const nextInput = findNextInput(this);
                    if (nextInput) {
                        nextInput.focus();
                    }
                }
            });
            
            // 方向鍵導航
            input.addEventListener('keydown', function(e) {
                let nextInput = null;
                
                if (e.key === 'ArrowDown') {
                    nextInput = findInputBelow(this);
                } else if (e.key === 'ArrowUp') {
                    nextInput = findInputAbove(this);
                } else if (e.key === 'ArrowRight' && this.selectionStart === this.value.length) {
                    nextInput = findInputRight(this);
                } else if (e.key === 'ArrowLeft' && this.selectionStart === 0) {
                    nextInput = findInputLeft(this);
                } else {
                    return; // 不是我們要處理的鍵
                }
                
                if (nextInput) {
                    e.preventDefault();
                    nextInput.focus();
                    // 游標放在末尾
                    nextInput.selectionStart = nextInput.value.length;
                    nextInput.selectionEnd = nextInput.value.length;
                }
            });
        }
    });
}

/**
 * 儲存成績到伺服器
 * 
 * @param {string} studentId - 學生ID
 * @param {string} gradeItemId - 成績項目ID
 * @param {string} value - 成績值
 * @param {HTMLElement} cell - 成績儲存格元素
 */
// 找尋下一個輸入框
function findNextInput(currentInput) {
    const allInputs = Array.from(document.querySelectorAll('.grade-cell input'));
    const currentIndex = allInputs.indexOf(currentInput);
    
    if (currentIndex !== -1 && currentIndex < allInputs.length - 1) {
        return allInputs[currentIndex + 1];
    }
    
    return null;
}

// 找尋下方的輸入框
function findInputBelow(currentInput) {
    const currentCell = currentInput.closest('td');
    const currentRow = currentCell.closest('tr');
    const cellIndex = Array.from(currentRow.cells).indexOf(currentCell);
    const nextRow = currentRow.nextElementSibling;
    
    if (nextRow && cellIndex !== -1) {
        const nextCell = nextRow.cells[cellIndex];
        if (nextCell) {
            const nextInput = nextCell.querySelector('input');
            if (nextInput) {
                return nextInput;
            }
        }
    }
    
    return null;
}

// 找尋上方的輸入框
function findInputAbove(currentInput) {
    const currentCell = currentInput.closest('td');
    const currentRow = currentCell.closest('tr');
    const cellIndex = Array.from(currentRow.cells).indexOf(currentCell);
    const prevRow = currentRow.previousElementSibling;
    
    if (prevRow && cellIndex !== -1) {
        const prevCell = prevRow.cells[cellIndex];
        if (prevCell) {
            const prevInput = prevCell.querySelector('input');
            if (prevInput) {
                return prevInput;
            }
        }
    }
    
    return null;
}

// 找尋右方的輸入框
function findInputRight(currentInput) {
    const currentCell = currentInput.closest('td');
    const nextCell = currentCell.nextElementSibling;
    
    if (nextCell) {
        const nextInput = nextCell.querySelector('input');
        if (nextInput) {
            return nextInput;
        }
    }
    
    return null;
}

// 找尋左方的輸入框
function findInputLeft(currentInput) {
    const currentCell = currentInput.closest('td');
    const prevCell = currentCell.previousElementSibling;
    
    if (prevCell) {
        const prevInput = prevCell.querySelector('input');
        if (prevInput) {
            return prevInput;
        }
    }
    
    return null;
}

function saveGrade(studentId, gradeItemId, value, cell) {
    const input = cell.querySelector('input');
    
    // 儲存過程禁用輸入
    input.disabled = true;
    
    // 顯示暫時視覺反饋
    input.classList.add('saving');
    
    // 準備伺服器資料
    const data = {
        student_id: parseInt(studentId),
        grade_item_id: parseInt(gradeItemId),
        value: value.trim() ? value : null
    };
    
    // 傳送到伺服器
    fetch('/teacher/grades', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify(data)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('伺服器傳回錯誤');
        }
        return response.json();
    })
    .then(result => {
        if (result.success) {
            // 更新儲存值
            input.defaultValue = input.value;
            
            // 成功儲存視覺反饋
            input.classList.remove('saving');
            input.classList.add('save-success');
            
            // 2秒後移除視覺反饋
            setTimeout(() => {
                input.classList.remove('save-success');
            }, 2000);
        } else {
            throw new Error(result.message || '未知錯誤');
        }
    })
    .catch(error => {
        console.error('儲存成績錯誤:', error);
        
        // 移除儲存中的視覺反饋
        input.classList.remove('saving');
        input.classList.add('save-error');
        
        // 警告錯誤訊息
        alert(`儲存成績錯誤: ${error.message}`);
        
        // 2秒後移除視覺反饋
        setTimeout(() => {
            input.classList.remove('save-error');
        }, 2000);
    })
    .finally(() => {
        // 重新啟用輸入
        input.disabled = false;
    });
}
