// Backend adresi. NEXT_PUBLIC_ ile başlayan değişkenler derleme anında koda gömülür,
// bu yüzden değiştirince geliştirme sunucusunu yeniden başlatmak gerekir.
export const API_URL = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/+$/, "");
