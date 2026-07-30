import { useMemo, useState } from 'react'
import { BarChart3, Filter, PlusCircle, Sparkles } from 'lucide-react'
import { mockBranches, mockChildren, mockDeals, mockParents, mockTariffs, mockUsers } from '../data/mockData'
import type { CurrentUser, Deal, PipelineId } from '../types'
import { pipelineLabels, stageLabels } from '../types'
import { CheckoutModal } from './CheckoutModal'
import { DealModal } from './DealModal'
import { KanbanBoard } from './KanbanBoard'

const pipelineOptions: PipelineId[] = ['school', 'kindergarten', 'b2b']

export function Dashboard() {
  const [deals, setDeals] = useState<Deal[]>(mockDeals)
  const [currentUser, setCurrentUser] = useState<CurrentUser>(mockUsers.salesManager)
  const [selectedDeal, setSelectedDeal] = useState<Deal | null>(null)
  const [modalMode, setModalMode] = useState<'edit' | 'create'>('edit')
  const [searchTerm, setSearchTerm] = useState('')
  const [pipelineFilter, setPipelineFilter] = useState<PipelineId>('school')
  const [branchFilter, setBranchFilter] = useState<string>('all')
  const [gradeFilter, setGradeFilter] = useState('All')
  const [waitlistedOnly, setWaitlistedOnly] = useState(false)
  const [pendingCheckout, setPendingCheckout] = useState<{ dealId: string; nextStageId: Deal['stageId'] } | null>(null)

  const branchOptions = currentUser.role === 'hq_admin' ? mockBranches : mockBranches.filter((branch) => currentUser.allowedBranchIds.includes(branch.id))

  const visibleDeals = useMemo(() => {
    return deals.filter((deal) => {
      const parent = mockParents.find((entry) => entry.id === deal.parentId)
      const child = mockChildren.find((entry) => entry.id === deal.childId)
      const matchesPipeline = deal.pipelineId === pipelineFilter
      const matchesBranch = branchFilter === 'all' || deal.branchId === branchFilter
      const matchesSearch = !searchTerm || `${parent?.name ?? ''} ${child?.name ?? ''}`.toLowerCase().includes(searchTerm.toLowerCase())
      const matchesGrade = gradeFilter === 'All' || child?.gradeOrGroup === gradeFilter
      const matchesWaitlist = !waitlistedOnly || deal.isWaitlisted
      return matchesPipeline && matchesBranch && matchesSearch && matchesGrade && matchesWaitlist
    })
  }, [branchFilter, deals, gradeFilter, pipelineFilter, searchTerm, waitlistedOnly])

  const stats = useMemo(() => {
    const total = visibleDeals.reduce((sum, deal) => sum + deal.expectedRevenue, 0)
    const success = visibleDeals.filter((deal) => ['contract-signed', 'entrance-fee-paid', 'enrolled'].includes(deal.stageId)).length
    const waitlisted = visibleDeals.filter((deal) => deal.isWaitlisted).length
    return { total, success, waitlisted }
  }, [visibleDeals])

  const canManage = currentUser.role === 'hq_admin' || currentUser.role === 'sales'

  const selectedParent = selectedDeal ? mockParents.find((entry) => entry.id === selectedDeal.parentId) ?? null : null
  const selectedChild = selectedDeal ? mockChildren.find((entry) => entry.id === selectedDeal.childId) ?? null : null
  const selectedBranch = selectedDeal ? mockBranches.find((entry) => entry.id === selectedDeal.branchId) ?? null : null
  const selectedTariff = selectedDeal ? mockTariffs.find((entry) => entry.id === selectedDeal.tariffId) ?? null : null
  const pendingDeal = pendingCheckout ? deals.find((deal) => deal.id === pendingCheckout.dealId) ?? null : null
  const pendingParent = pendingDeal ? mockParents.find((entry) => entry.id === pendingDeal.parentId) ?? null : null
  const pendingChild = pendingDeal ? mockChildren.find((entry) => entry.id === pendingDeal.childId) ?? null : null
  const pendingTariff = pendingDeal ? mockTariffs.find((entry) => entry.id === pendingDeal.tariffId) ?? null : null

  const openDeal = (deal: Deal) => {
    setSelectedDeal(deal)
    setModalMode('edit')
  }

  const closeModal = () => {
    setSelectedDeal(null)
    setModalMode('edit')
  }

  const updateDeal = (dealId: string, updater: (deal: Deal) => Deal) => {
    setDeals((current) => current.map((deal) => (deal.id === dealId ? updater(deal) : deal)))
  }

  const handleStageChange = (dealId: string, nextStageId: Deal['stageId']) => {
    if (nextStageId === 'contract-signed' || nextStageId === 'entrance-fee-paid') {
      setPendingCheckout({ dealId, nextStageId })
      return
    }

    updateDeal(dealId, (deal) => ({
      ...deal,
      stageId: nextStageId,
      history: [...deal.history, { id: `${deal.id}-${nextStageId}`, type: 'Sales', description: `Stage changed to ${stageLabels[nextStageId]}`, timestamp: new Date().toISOString() }],
    }))
  }

  const handleCheckoutConfirm = () => {
    if (!pendingCheckout) return

    updateDeal(pendingCheckout.dealId, (deal) => ({
      ...deal,
      stageId: pendingCheckout.nextStageId,
      history: [...deal.history, { id: `${deal.id}-${pendingCheckout.nextStageId}`, type: 'System', description: `Enrollment flow completed for ${stageLabels[pendingCheckout.nextStageId]}`, timestamp: new Date().toISOString() }],
    }))
    setPendingCheckout(null)
  }

  const handleCreateDeal = (newDeal: Deal) => {
    setDeals((current) => [newDeal, ...current])
  }

  const handleSaveDeal = (updatedDeal: Deal) => {
    setDeals((current) => current.map((deal) => (deal.id === updatedDeal.id ? updatedDeal : deal)))
  }

  const handleDeleteDeal = (dealId: string) => {
    setDeals((current) => current.filter((deal) => deal.id !== dealId))
    setSelectedDeal(null)
  }

  return (
    <div className="min-h-screen bg-transparent p-6 text-slate-900">
      <div className="mx-auto max-w-7xl space-y-6">
        <header className="rounded-3xl border border-slate-200 bg-white/80 p-6 shadow-sm backdrop-blur">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <div className="mb-2 flex items-center gap-2 text-sm font-medium text-slate-500">
                <Sparkles size={16} /> BI Education CRM Demo
              </div>
              <h1 className="text-3xl font-semibold tracking-tight">Educational sales CRM</h1>
              <p className="mt-2 text-sm text-slate-600">Parent → child → deal workflow with branch-aware permissions and checkout-style enrollment stages.</p>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <button type="button" onClick={() => setCurrentUser(currentUser.id === mockUsers.salesManager.id ? mockUsers.hqAdmin : mockUsers.salesManager)} className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm font-medium text-slate-700">
                {currentUser.role === 'hq_admin' ? 'Switch to sales manager' : 'Switch to HQ admin'}
              </button>
              <label className="flex items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-700">
                <Filter size={15} />
                <select value={branchFilter} onChange={(event) => setBranchFilter(event.target.value)} className="bg-transparent outline-none">
                  <option value="all">All branches</option>
                  {branchOptions.map((branch) => (
                    <option key={branch.id} value={branch.id}>{branch.name}</option>
                  ))}
                </select>
              </label>
              <button onClick={() => { setSelectedDeal(null); setModalMode('create') }} className="inline-flex items-center gap-2 rounded-xl bg-slate-900 px-4 py-2 text-sm font-medium text-white shadow-sm">
                <PlusCircle size={16} /> New deal
              </button>
            </div>
          </div>

          <div className="mt-5 flex flex-wrap gap-2">
            {pipelineOptions.map((pipeline) => (
              <button key={pipeline} type="button" onClick={() => setPipelineFilter(pipeline)} className={`rounded-full px-3 py-2 text-sm font-medium ${pipelineFilter === pipeline ? 'bg-slate-900 text-white' : 'bg-slate-100 text-slate-700'}`}>
                {pipelineLabels[pipeline]}
              </button>
            ))}
          </div>

          <div className="mt-5 flex flex-wrap gap-3">
            <input value={searchTerm} onChange={(event) => setSearchTerm(event.target.value)} placeholder="Search parent or child" className="w-full max-w-sm rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm outline-none" />
            <select value={gradeFilter} onChange={(event) => setGradeFilter(event.target.value)} className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm outline-none">
              <option value="All">All grades</option>
              <option value="1st Grade">1st Grade</option>
              <option value="2nd Grade">2nd Grade</option>
              <option value="Preschool Group">Preschool Group</option>
              <option value="Middle Group">Middle Group</option>
            </select>
            <label className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700">
              <input type="checkbox" checked={waitlistedOnly} onChange={() => setWaitlistedOnly((value) => !value)} />
              Waitlisted only
            </label>
          </div>

          <div className="mt-6 grid gap-4 md:grid-cols-3">
            <div className="rounded-2xl bg-slate-50 p-4">
              <p className="text-sm text-slate-500">Visible deals</p>
              <p className="mt-1 text-2xl font-semibold">{visibleDeals.length}</p>
            </div>
            <div className="rounded-2xl bg-slate-50 p-4">
              <p className="text-sm text-slate-500">Closed / won</p>
              <p className="mt-1 text-2xl font-semibold">{stats.success}</p>
            </div>
            <div className="rounded-2xl bg-slate-50 p-4">
              <p className="text-sm text-slate-500">Waitlisted</p>
              <p className="mt-1 text-2xl font-semibold">{stats.waitlisted}</p>
            </div>
          </div>

          <div className="mt-4 flex items-center gap-2 rounded-2xl border border-emerald-100 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
            <BarChart3 size={16} />
            <span>Projected pipeline value: {stats.total.toLocaleString('ru-RU')} ₸</span>
          </div>
        </header>

        <KanbanBoard deals={visibleDeals} currentUser={currentUser} pipelineId={pipelineFilter} onSelectDeal={openDeal} onStageChange={handleStageChange} />
      </div>

      <DealModal
        deal={selectedDeal}
        mode={modalMode}
        currentUser={currentUser}
        parent={selectedParent}
        child={selectedChild}
        branch={selectedBranch}
        tariff={selectedTariff}
        onClose={closeModal}
        onDeleteDeal={handleDeleteDeal}
        onSaveDeal={handleSaveDeal}
        onCreateDeal={handleCreateDeal}
        canManage={canManage}
      />

      <CheckoutModal
        deal={pendingDeal}
        parent={pendingParent}
        child={pendingChild}
        tariff={pendingTariff}
        onCancel={() => setPendingCheckout(null)}
        onConfirm={handleCheckoutConfirm}
      />
    </div>
  )
}
