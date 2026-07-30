import { useEffect, useMemo, useState } from 'react'
import { X } from 'lucide-react'
import type { Child, CurrentUser, Deal, Parent } from '../types'
import { apiClient } from '../api/client'

interface DealModalProps {
  deal: Deal | null
  mode?: 'edit' | 'create'
  currentUser: CurrentUser
  parent: Parent | null
  child: Child | null
  branch: any | null
  tariff: any | null
  canManage: boolean
  onClose: () => void
  onDeleteDeal?: (dealId: string) => void
  onSaveDeal?: (deal: Deal) => void
  onCreateDeal?: (deal: Deal) => void
}

export function DealModal(props: DealModalProps) {
  const { deal, mode = 'edit', currentUser, parent, child, branch, tariff, canManage, onClose, onDeleteDeal, onSaveDeal, onCreateDeal } = props
  const isCreateMode = mode === 'create'
  const [activeTab, setActiveTab] = useState<'timeline' | 'tasks'>('timeline')
  const [draft, setDraft] = useState<Deal | null>(deal)
  const [branches, setBranches] = useState<any[]>([])
  const [tariffs, setTariffs] = useState<any[]>([])
  const [selectedBranchCode, setSelectedBranchCode] = useState<string | null>(branch?.code ?? null)
  const [selectedTariffName, setSelectedTariffName] = useState<string | null>(tariff?.name ?? null)

  useEffect(() => {
    setDraft(deal)
  }, [deal])

  useEffect(() => {
    let mounted = true
    apiClient.get('deals/metadata').then((res) => {
      if (!mounted) return
      const loadedBranches = res.data.branches || []
      const loadedTariffs = res.data.tariffs || []
      setBranches(loadedBranches)
      setTariffs(loadedTariffs)
      // initialize default selections
      if (!selectedBranchCode && loadedBranches.length) {
        const defaultBranch = loadedBranches[0]
        setSelectedBranchCode(defaultBranch.code)
        const firstTariff = loadedTariffs.find((t: any) => t.branch_id === defaultBranch.id)
        if (firstTariff) setSelectedTariffName(firstTariff.name)
      }
    }).catch(() => {})
    return () => { mounted = false }
  }, [])

  // when branch changes, pick first tariff for that branch
  useEffect(() => {
    if (!selectedBranchCode || !tariffs.length || !branches.length) return
    const branchObj = branches.find((b) => b.code === selectedBranchCode)
    if (!branchObj) return
    const firstTariff = tariffs.find((t) => t.branch_id === branchObj.id)
    if (firstTariff && firstTariff.name !== selectedTariffName) setSelectedTariffName(firstTariff.name)
  }, [selectedBranchCode, tariffs, branches])

  const displayDeal = useMemo(() => {
    if (draft) return draft
    if (isCreateMode) {
      return {
        id: `deal-${Date.now()}`,
        parentId: '',
        childId: '',
        branchId: branch?.id ?? branches[0]?.id ?? 'riviera',
        pipelineId: 'school' as const,
        stageId: 'new-lead' as const,
        tariffId: tariff?.id ?? tariffs[0]?.id ?? 't1',
        addons: { food: false, transport: false },
        isWaitlisted: false,
        expectedRevenue: 0,
        tasks: [],
        history: [{ id: 'init', type: 'System', description: 'New deal created in the CRM', timestamp: new Date().toISOString() }],
      } as Deal
    }
    return null
  }, [branch?.id, draft, isCreateMode, tariff?.id, branches, tariffs])

  useEffect(() => {
    if (!displayDeal) return
    const branchCode = selectedBranchCode || branch?.code
    const tariffName = selectedTariffName || tariff?.name
    apiClient.post('deals/pricing', { branch: branchCode, tariff: tariffName, has_food: displayDeal.addons.food, has_transport: displayDeal.addons.transport, grade: child?.gradeOrGroup ?? child?.gradeOrGroup }).then((res) => {
      const total = res.data && (res.data.total_amount || res.data.total)
      if (total) setDraft(current => current ? ({ ...current, expectedRevenue: Number(total) }) : current)
    }).catch(() => {})
  }, [selectedBranchCode, selectedTariffName, draft?.addons?.food, draft?.addons?.transport, child?.gradeOrGroup])

  if (!displayDeal && !isCreateMode) return null

  const handleToggleTask = (taskId: string) => {
    if (!displayDeal) return
    setDraft((current) => current ? ({ ...current, tasks: current.tasks.map((task) => task.id === taskId ? { ...task, isDone: !task.isDone } : task) }) : current)
  }

  const handleSave = () => {
    if (!displayDeal) return
    if (isCreateMode) {
      onCreateDeal?.(displayDeal)
    } else {
      onSaveDeal?.(displayDeal)
    }
    onClose()
  }

  const canEdit = canManage || currentUser.role === 'sales'

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 p-4">
      <div className="w-full max-w-5xl rounded-3xl bg-white p-6 shadow-2xl">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-sm font-medium text-slate-500">{isCreateMode ? 'New deal' : 'Deal details'}</p>
            <h2 className="text-2xl font-semibold text-slate-900">{parent?.name ?? 'Create a new educational opportunity'}</h2>
            <p className="mt-1 text-sm text-slate-500">{child?.name ?? 'No child linked yet'} • {branch?.name ?? 'No branch'}</p>
          </div>
          <button onClick={onClose} className="rounded-full p-2 hover:bg-slate-100">
            <X size={18} />
          </button>
        </div>

        <div className="mt-6 flex gap-2 rounded-full bg-slate-100 p-1">
          <button type="button" onClick={() => setActiveTab('timeline')} className={`rounded-full px-3 py-2 text-sm font-medium ${activeTab === 'timeline' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-600'}`}>Timeline</button>
          <button type="button" onClick={() => setActiveTab('tasks')} className={`rounded-full px-3 py-2 text-sm font-medium ${activeTab === 'tasks' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-600'}`}>Tasks</button>
        </div>

        <div className="mt-6 grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
          <div className="rounded-2xl border border-slate-200 p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-500">Summary</p>
                <h3 className="text-lg font-semibold text-slate-900">{selectedTariffName ?? tariff?.name ?? 'No tariff selected'}</h3>
              </div>
              <div className="text-right">
                <p className="text-sm text-slate-500">Expected total</p>
                <p className="text-xl font-semibold text-slate-900">{Number(displayDeal?.expectedRevenue || 0).toLocaleString('ru-RU')} ₸</p>
              </div>
            </div>

            <div className="mt-4 grid gap-3">
              <div>
                <label className="block text-sm text-slate-600">Branch</label>
                <select value={selectedBranchCode ?? ''} onChange={(e) => { setSelectedBranchCode(e.target.value); setSelectedTariffName(null) }} className="mt-1 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm">
                  <option value="">Select branch</option>
                  {branches.map((b) => (<option key={b.id} value={b.code}>{b.name} — {b.city}</option>))}
                </select>
              </div>

              <div>
                <label className="block text-sm text-slate-600">Tariff</label>
                <select value={selectedTariffName ?? ''} onChange={(e) => setSelectedTariffName(e.target.value)} className="mt-1 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm">
                  <option value="">Select tariff</option>
                  {tariffs.filter((t) => {
                    if (!selectedBranchCode) return true
                    const branchForTariff = branches.find((b) => b.id === t.branch_id)
                    return branchForTariff && branchForTariff.code === selectedBranchCode
                  }).map((t) => (<option key={t.id} value={t.name}>{t.name} — {t.base_amount ? Number(t.base_amount).toLocaleString('ru-RU') : ''} ₸</option>))}
                </select>
              </div>

              <div className="rounded-2xl bg-slate-50 p-4 text-sm text-slate-600">
                <div className="flex items-center justify-between">
                  <span>Food</span>
                  <label className="font-medium text-slate-900"><input type="checkbox" checked={displayDeal?.addons.food} onChange={(e) => setDraft(current => current ? ({ ...current, addons: { ...current.addons, food: e.target.checked } }) : current)} className="mr-2" />{displayDeal?.addons.food ? 'Included' : 'Not selected'}</label>
                </div>
                <div className="mt-2 flex items-center justify-between">
                  <span>Transport</span>
                  <label className="font-medium text-slate-900"><input type="checkbox" checked={displayDeal?.addons.transport} onChange={(e) => setDraft(current => current ? ({ ...current, addons: { ...current.addons, transport: e.target.checked } }) : current)} className="mr-2" />{displayDeal?.addons.transport ? 'Included' : 'Not selected'}</label>
                </div>
                <div className="mt-2 flex items-center justify-between">
                  <span>Waitlist</span>
                  <label className="font-medium text-slate-900"><input type="checkbox" checked={displayDeal?.isWaitlisted} onChange={(e) => setDraft(current => current ? ({ ...current, isWaitlisted: e.target.checked }) : current)} className="mr-2" />{displayDeal?.isWaitlisted ? 'Yes' : 'No'}</label>
                </div>
              </div>

              <div className="mt-2 flex items-center justify-between px-2">
                <div className="text-sm text-slate-500">Entrance fee</div>
                <div className="font-semibold text-slate-900">{tariffs.find(t => t.name === selectedTariffName)?.entrance_fee ? Number(tariffs.find(t => t.name === selectedTariffName)?.entrance_fee).toLocaleString('ru-RU') : '—'} ₸</div>
              </div>
            </div>
          </div>

          <div className="rounded-2xl border border-slate-200 p-4">
            {activeTab === 'timeline' ? (
              <div className="space-y-3">{displayDeal?.history.map((entry) => (<div key={entry.id} className="rounded-xl bg-slate-50 p-3 text-sm text-slate-700"><div className="flex items-center justify-between"><span className="font-medium text-slate-900">{entry.type}</span><span className="text-xs text-slate-500">{new Date(entry.timestamp).toLocaleDateString('ru-RU')}</span></div><p className="mt-1">{entry.description}</p></div>))}</div>
            ) : (
              <div className="space-y-3">{displayDeal?.tasks.length ? displayDeal.tasks.map((task) => (<label key={task.id} className="flex items-center justify-between rounded-xl border border-slate-200 px-3 py-3 text-sm text-slate-700"><span className="flex items-center gap-2"><input type="checkbox" checked={task.isDone} onChange={() => handleToggleTask(task.id)} /><span>{task.title}</span></span><span className="text-slate-500">{task.dueDate}</span></label>)) : <p className="text-sm text-slate-500">No tasks yet.</p>}</div>
            )}
          </div>
        </div>

        <div className="mt-6 flex flex-wrap items-center justify-between gap-3">
          <div className="flex gap-2">
            {canManage ? (<button type="button" onClick={() => onDeleteDeal?.(displayDeal?.id ?? '')} className="rounded-lg border border-rose-200 px-4 py-2 text-sm font-medium text-rose-700">Delete deal</button>) : null}
            {canEdit ? (<button type="button" className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700">Apply custom discount</button>) : null}
          </div>
          <div className="flex gap-3">
            <button onClick={onClose} className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700">Cancel</button>
            <button onClick={handleSave} className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white">{isCreateMode ? 'Create deal' : 'Save changes'}</button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default DealModal
