' VBScript崩溃测试程序
' 双击即可运行，会触发错误

' 显示提示
WScript.Echo "即将触发运行时错误..."
WScript.Sleep 1000

' 方法1: 除以零
On Error Resume Next
Dim result
result = 1 / 0
On Error Goto 0

' 方法2: 访问不存在的对象
Set obj = CreateObject("NonExistent.Application")
obj.DoSomething

' 方法3: 数组越界
Dim arr(5)
For i = 0 To 100
    arr(i) = i
Next

' 方法4: 强制错误
Err.Raise 9999, "Test", "Manual error trigger"

