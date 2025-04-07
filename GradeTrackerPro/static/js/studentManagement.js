/**
 * 成績管理系統 - 學生管理腳本
 * 
 * 負責處理學生管理頁面的互動功能：
 * - 班級和學生資料操作
 * - 批次學生導入
 * - 班級管理
 */

$(document).ready(function() {
    // 初始化DataTables
    if ($("#studentsTable").length) {
        $("#studentsTable").DataTable({
            language: {
                "search": "搜尋:",
                "lengthMenu": "顯示 _MENU_ 筆資料",
                "info": "顯示第 _START_ 至 _END_ 筆資料，共 _TOTAL_ 筆",
                "infoEmpty": "沒有資料",
                "infoFiltered": "(從 _MAX_ 筆資料中過濾)",
                "zeroRecords": "沒有符合的資料",
                "paginate": {
                    "first": "第一頁",
                    "last": "最後一頁",
                    "next": "下一頁",
                    "previous": "上一頁"
                }
            }
        });
    }

    // 學期選擇器變更
    $("#semesterSelector").on("change", function() {
        const semester = $(this).val();
        window.location.href = `/student_management?semester=${encodeURIComponent(semester)}`;
    });

    // 班級選擇器變更
    $("#classSelector").on("change", function() {
        const classId = $(this).val();
        const semester = $("#semesterSelector").val();
        window.location.href = `/student_management?semester=${encodeURIComponent(semester)}&class_id=${classId}`;
    });

    // 批次管理學生儲存
    $("#saveBatchStudents").on("click", function() {
        const classId = $("#classSelector").val();
        if (!classId) {
            alert("請先選擇班級");
            return;
        }

        const batchStudentData = $("#batchStudentData").val().trim();
        if (!batchStudentData) {
            alert("請輸入學生資料");
            return;
        }

        const clearExistingStudents = $("#clearExistingStudents").is(":checked");
        
        // 顯示處理中的狀態
        const originalButtonText = $(this).text();
        $(this).html('<i class="fas fa-spinner fa-spin me-1"></i>處理中...');
        $(this).prop('disabled', true);

        // 解析批次資料
        const students = [];
        const lines = batchStudentData.split("\n");
        let hasError = false;
        let errorMessage = "";
        
        for (let i = 0; i < lines.length; i++) {
            const line = lines[i].trim();
            if (!line) continue;
            
            const parts = line.split(",");
            if (parts.length < 3) {
                errorMessage = `第${i+1}行格式錯誤：${line}\n應為：班級座號,姓名,學號`;
                hasError = true;
                break;
            }
            
            const seatNumber = parts[0].trim();
            const name = parts[1].trim();
            const studentId = parts[2].trim();
            
            // 驗證座號格式（五碼）
            if (!/^\d{5}$/.test(seatNumber)) {
                errorMessage = `第${i+1}行座號格式錯誤：${seatNumber}\n應為五碼數字，例如30102`;
                hasError = true;
                break;
            }
            
            // 驗證學號格式（六碼）
            if (!/^\d{6}$/.test(studentId)) {
                errorMessage = `第${i+1}行學號格式錯誤：${studentId}\n應為六碼數字，例如111230`;
                hasError = true;
                break;
            }
            
            students.push({
                seatNumber,
                name,
                studentId
            });
        }
        
        if (hasError) {
            alert(errorMessage);
            // 恢復按鈕狀態
            $(this).html(originalButtonText);
            $(this).prop('disabled', false);
            return;
        }
        
        // 為使用者顯示確認對話框
        const confirmMessage = `即將處理 ${students.length} 位學生的資料。` + 
                            (clearExistingStudents ? "此操作將清除班級中所有現有學生資料！" : "") + 
                            "\n確定要繼續嗎？";
                            
        if (!confirm(confirmMessage)) {
            // 恢復按鈕狀態
            $(this).html(originalButtonText);
            $(this).prop('disabled', false);
            return;
        }
        
        // 發送請求到後端
        $.ajax({
            url: "/api/students/batch",
            method: "POST",
            contentType: "application/json",
            data: JSON.stringify({
                classId,
                students,
                clearExisting: clearExistingStudents
            }),
            success: function(response) {
                // 顯示詳細結果
                alert(`學生資料已成功處理!\n${response.message}`);
                $("#batchStudentModal").modal("hide");
                window.location.reload();
            },
            error: function(xhr) {
                alert("匯入失敗：" + (xhr.responseJSON?.message || "未知錯誤"));
                // 恢復按鈕狀態
                $("#saveBatchStudents").html(originalButtonText);
                $("#saveBatchStudents").prop('disabled', false);
            }
        });
    });

    // 編輯單一學生
    $(".edit-student").on("click", function() {
        const studentId = $(this).data("student-id");
        
        // 向後端獲取學生資料
        $.ajax({
            url: `/api/students/${studentId}`,
            method: "GET",
            success: function(student) {
                $("#studentId").val(student.id);
                $("#seatNumber").val(student.seat_number);
                $("#studentName").val(student.name);
                $("#studentIdInput").val(student.student_id);
                
                $("#studentEditModal").modal("show");
            },
            error: function() {
                alert("無法載入學生資料");
            }
        });
    });

    // 儲存學生編輯
    $("#saveStudent").on("click", function() {
        const studentId = $("#studentId").val();
        const seatNumber = $("#seatNumber").val();
        const name = $("#studentName").val();
        const studentIdNumber = $("#studentIdInput").val();
        
        // 驗證座號格式（五碼）
        if (!/^\d{5}$/.test(seatNumber)) {
            alert("座號格式錯誤，應為五碼數字");
            return;
        }
        
        // 驗證學號格式（六碼）
        if (!/^\d{6}$/.test(studentIdNumber)) {
            alert("學號格式錯誤，應為六碼數字");
            return;
        }
        
        // 發送請求到後端
        $.ajax({
            url: `/api/students/${studentId}`,
            method: "PUT",
            contentType: "application/json",
            data: JSON.stringify({
                seatNumber,
                name,
                studentId: studentIdNumber
            }),
            success: function() {
                alert("學生資料已更新");
                $("#studentEditModal").modal("hide");
                window.location.reload();
            },
            error: function(xhr) {
                alert("更新失敗：" + (xhr.responseJSON?.message || "未知錯誤"));
            }
        });
    });

    // 刪除學生
    $(".delete-student").on("click", function() {
        if (!confirm("確定要刪除此學生嗎？")) return;
        
        const studentId = $(this).data("student-id");
        
        $.ajax({
            url: `/api/students/${studentId}`,
            method: "DELETE",
            success: function() {
                alert("學生已刪除");
                window.location.reload();
            },
            error: function() {
                alert("刪除失敗");
            }
        });
    });

    // 新增班級
    $("#saveNewClass").on("click", function() {
        const className = $("#newClassName").val();
        const semester = $("#newClassSemester").val();
        
        if (!className) {
            alert("請輸入班級名稱");
            return;
        }
        
        $.ajax({
            url: "/api/classes",
            method: "POST",
            contentType: "application/json",
            data: JSON.stringify({
                name: className,
                semester: semester
            }),
            success: function() {
                alert("班級已創建");
                $("#addClassModal").modal("hide");
                window.location.reload();
            },
            error: function() {
                alert("班級創建失敗");
            }
        });
    });

    // 儲存班級編輯
    $("#saveClassInfo").on("click", function() {
        const classId = $("#classSelector").val();
        const className = $("#className").val();
        
        if (!className) {
            alert("請輸入班級名稱");
            return;
        }
        
        $.ajax({
            url: `/api/classes/${classId}`,
            method: "PUT",
            contentType: "application/json",
            data: JSON.stringify({
                name: className
            }),
            success: function() {
                alert("班級資料已更新");
                $("#editClassModal").modal("hide");
                window.location.reload();
            },
            error: function() {
                alert("更新失敗");
            }
        });
    });

    // 新增學期
    $("#saveNewSemester").on("click", function() {
        const semester = $("#newSemester").val();
        
        if (!semester) {
            alert("請輸入學期");
            return;
        }
        
        $.ajax({
            url: "/api/semesters",
            method: "POST",
            contentType: "application/json",
            data: JSON.stringify({ semester }),
            success: function() {
                alert("學期已創建");
                $("#addSemesterModal").modal("hide");
                window.location.reload();
            },
            error: function() {
                alert("學期創建失敗");
            }
        });
    });
});