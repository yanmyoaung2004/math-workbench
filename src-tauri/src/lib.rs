// Learn more about Tauri commands at https://tauri.app/develop/calling-rust/
#[tauri::command]
fn engine_ping() -> String {
    "workbench-engine-shell-ok".to_string()
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        // Updater is initialized but inert: no endpoints/pubkey configured until
        // release signing exists (see docs/packaging.md). No UI calls check().
        .plugin(tauri_plugin_updater::Builder::new().build())
        .invoke_handler(tauri::generate_handler![engine_ping])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
