import type { Activity, Branch, Child, CurrentUser, Deal, Parent, Tariff, Task } from '../types'

export const mockBranches: Branch[] = [
  { id: 'riviera', name: 'Riviera', city: 'Astana', segment: 'School' },
  { id: 'quantum', name: 'Quantum', city: 'Astana', segment: 'STEM' },
  { id: 'aldi', name: 'ALDI BI', city: 'Almaty', segment: 'Kindergarten' },
  { id: 'biart', name: 'BIART', city: 'Astana', segment: 'B2B' },
]

export const mockParents: Parent[] = [
  { id: 'p1', name: 'Aigerim Tolegenova', phone: '+7 701 111 22 33' },
  { id: 'p2', name: 'Nurlan Bektemirov', phone: '+7 707 222 44 55' },
  { id: 'p3', name: 'Madiyar Sarsenov', phone: '+7 700 333 66 77' },
  { id: 'p4', name: 'Dana Khamzina', phone: '+7 705 444 88 99' },
]

export const mockChildren: Child[] = [
  { id: 'c1', parentId: 'p1', name: 'Aruzhan Tolegenova', birthDate: '2020-01-15', gradeOrGroup: '1st Grade', medicalNotes: 'No allergies' },
  { id: 'c2', parentId: 'p2', name: 'Yerasyl Bektemirov', birthDate: '2018-09-21', gradeOrGroup: 'Middle Group', medicalNotes: 'Needs morning snacks' },
  { id: 'c3', parentId: 'p3', name: 'Samal Sarsenova', birthDate: '2022-03-05', gradeOrGroup: 'Preschool Group', medicalNotes: '' },
  { id: 'c4', parentId: 'p4', name: 'Arman Khamzin', birthDate: '2019-07-11', gradeOrGroup: '2nd Grade', medicalNotes: 'Asthma plan on file' },
]

export const mockTariffs: Tariff[] = [
  { id: 't1', branchId: 'riviera', name: 'Выгодный', basePrice: 180000, entranceFee: 40000 },
  { id: 't2', branchId: 'riviera', name: 'Стандарт', basePrice: 240000, entranceFee: 50000 },
  { id: 't3', branchId: 'quantum', name: 'Стандарт', basePrice: 260000, entranceFee: 60000 },
  { id: 't4', branchId: 'aldi', name: 'Выгодный', basePrice: 175000, entranceFee: 35000 },
  { id: 't5', branchId: 'biart', name: 'Корпоративный', basePrice: 980000, entranceFee: 150000 },
]

const mockTasks = (title: string, dueDate: string): Task => ({ id: `${title}-${dueDate}`, title, isDone: false, dueDate })

const mockActivities = (description: string, timestamp: string): Activity => ({ id: `${description}-${timestamp}`, type: 'System', description, timestamp })

export const mockDeals: Deal[] = [
  {
    id: 'd1',
    parentId: 'p1',
    childId: 'c1',
    branchId: 'riviera',
    pipelineId: 'school',
    stageId: 'qualification',
    tariffId: 't2',
    addons: { food: true, transport: true },
    isWaitlisted: false,
    expectedRevenue: 290000,
    tasks: [mockTasks('Call back tomorrow', '2026-08-01'), mockTasks('Send payment link', '2026-08-02')],
    history: [mockActivities('WhatsApp Bot sent intake message', '2026-07-28T09:00:00Z'), mockActivities('Stage changed to Qualification', '2026-07-29T10:30:00Z')],
  },
  {
    id: 'd2',
    parentId: 'p2',
    childId: 'c2',
    branchId: 'aldi',
    pipelineId: 'kindergarten',
    stageId: 'trial-day',
    tariffId: 't4',
    addons: { food: true, transport: false },
    isWaitlisted: true,
    expectedRevenue: 210000,
    tasks: [mockTasks('Confirm trial slot', '2026-07-31')],
    history: [mockActivities('Trial day booked', '2026-07-27T16:45:00Z')],
  },
  {
    id: 'd3',
    parentId: 'p3',
    childId: 'c3',
    branchId: 'biart',
    pipelineId: 'b2b',
    stageId: 'offer',
    tariffId: 't5',
    addons: { food: false, transport: true },
    isWaitlisted: false,
    expectedRevenue: 980000,
    tasks: [mockTasks('Send proposal PDF', '2026-08-03')],
    history: [mockActivities('B2B intro call completed', '2026-07-25T15:00:00Z')],
  },
  {
    id: 'd4',
    parentId: 'p4',
    childId: 'c4',
    branchId: 'quantum',
    pipelineId: 'school',
    stageId: 'contract-signed',
    tariffId: 't3',
    addons: { food: false, transport: true },
    isWaitlisted: false,
    expectedRevenue: 320000,
    tasks: [mockTasks('Collect signed contract', '2026-08-05')],
    history: [mockActivities('Contract signed', '2026-07-30T11:00:00Z')],
  },
  {
    id: 'd5',
    parentId: 'p1',
    childId: 'c1',
    branchId: 'riviera',
    pipelineId: 'school',
    stageId: 'new-lead',
    tariffId: 't1',
    addons: { food: false, transport: false },
    isWaitlisted: false,
    expectedRevenue: 180000,
    tasks: [mockTasks('Send intro packet', '2026-08-06')],
    history: [mockActivities('Bot asked for preferred start date', '2026-07-29T12:00:00Z')],
  },
  {
    id: 'd6',
    parentId: 'p2',
    childId: 'c2',
    branchId: 'quantum',
    pipelineId: 'school',
    stageId: 'entrance-fee-paid',
    tariffId: 't3',
    addons: { food: true, transport: true },
    isWaitlisted: false,
    expectedRevenue: 360000,
    tasks: [mockTasks('Confirm payment receipt', '2026-08-08')],
    history: [mockActivities('Entrance fee payment received', '2026-07-30T15:45:00Z')],
  },
  {
    id: 'd7',
    parentId: 'p3',
    childId: 'c3',
    branchId: 'aldi',
    pipelineId: 'kindergarten',
    stageId: 'lost',
    tariffId: 't4',
    addons: { food: false, transport: false },
    isWaitlisted: false,
    expectedRevenue: 95000,
    tasks: [mockTasks('Close as lost', '2026-08-02')],
    history: [mockActivities('Parent declined after trial visit', '2026-07-28T08:40:00Z')],
  },
  {
    id: 'd8',
    parentId: 'p4',
    childId: 'c4',
    branchId: 'biart',
    pipelineId: 'b2b',
    stageId: 'enrolled',
    tariffId: 't5',
    addons: { food: true, transport: true },
    isWaitlisted: false,
    expectedRevenue: 1120000,
    tasks: [mockTasks('Prepare onboarding plan', '2026-08-10')],
    history: [mockActivities('B2B onboarding package sent', '2026-07-31T10:30:00Z')],
  },
]

export const mockUsers: Record<'salesManager' | 'hqAdmin', CurrentUser> = {
  salesManager: {
    id: 'u1',
    name: 'Sales Manager (Local)',
    role: 'sales',
    allowedBranchIds: ['riviera', 'aldi'],
  },
  hqAdmin: {
    id: 'u2',
    name: 'HQ Admin (Global)',
    role: 'hq_admin',
    allowedBranchIds: ['riviera', 'quantum', 'aldi', 'biart'],
  },
}
