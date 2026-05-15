import {usePathname, useRouter} from '@/i18n/routing';

export function LanguageSwitcher() {
  const router = useRouter();
  const pathname = usePathname();
  
  const handleLanguageChange = (locale: string) => {
    router.replace(pathname, {locale});
  };

  return (
    <div className="flex items-center gap-2 text-sm">
      <button 
        onClick={() => handleLanguageChange('vi')}
        className="hover:text-primary transition-colors font-medium"
      >
        VI
      </button>
      <span className="text-muted-foreground">|</span>
      <button 
        onClick={() => handleLanguageChange('en')}
        className="hover:text-primary transition-colors font-medium"
      >
        EN
      </button>
    </div>
  );
}
