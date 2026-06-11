import { NavLink } from 'react-router-dom'
import { LayoutDashboard, Briefcase, UserSearch, Settings } from 'lucide-react'

const navItems = [
  { to: '/', label: '系统监控', icon: LayoutDashboard },
  { to: '/jobs', label: '岗位匹配', icon: Briefcase },
  { to: '/resumes', label: '简历推荐', icon: UserSearch },
  { to: '/generator', label: '生成器控制', icon: Settings },
]

export default function Navbar() {
  return (
    <header className="sticky top-0 z-50" style={{ background: 'var(--card)', borderBottom: '1px solid var(--border)' }}>
      <div className="mx-auto px-6 h-[52px] flex items-center justify-between" style={{ maxWidth: '1300px' }}>
        <div className="font-semibold tracking-tight" style={{ color: 'var(--foreground)', fontSize: '1.125rem' }}>
          简历-岗位匹配系统
        </div>
        <nav className="flex items-center">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) =>
                `inline-flex items-center gap-1.5 px-4 py-2 text-sm transition-colors ${
                  isActive
                    ? 'font-medium'
                    : ''
                }`
              }
              style={({ isActive }) => ({
                color: isActive ? 'var(--accent)' : 'var(--muted-foreground)',
                background: isActive ? 'transparent' : 'transparent',
              })}
            >
              <item.icon className="h-4 w-4" />
              {item.label}
            </NavLink>
          ))}
        </nav>
      </div>
    </header>
  )
}